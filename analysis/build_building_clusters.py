#!/usr/bin/env python3
"""CHQ patterns from the six observed building-only attributes.

No source rows are published. Re-run with --scores pointing to the existing
building-only parquet. Only aggregate CSV/JSON/PNG/SVG outputs enter the site.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score,
                             davies_bouldin_score, silhouette_score)
from threadpoolctl import threadpool_limits

threadpool_limits(2)
SEED = 20261028
FEATURES = ['walls_energy_eff', 'windows_energy_eff', 'mainheat_energy_eff',
            'mainheatc_energy_eff', 'hot_water_energy_eff', 'lighting_energy_eff']
LABELS = ['Walls', 'Windows', 'Main heating', 'Heating controls', 'Hot water', 'Lighting']
SIL_TOLERANCE = .02
MIN_SHARE = .02
MIN_ARI = .80
BOOTSTRAPS = 20
COLORS = ['#216e6a', '#cc8132', '#7956a4', '#bb4c55', '#467abd', '#7a8541', '#626e7b']


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def fit(x, weights, k, seed=SEED, n_init=30):
    return KMeans(n_clusters=k, n_init=n_init, random_state=seed,
                  algorithm='lloyd', max_iter=500).fit(x, sample_weight=weights)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scores', type=Path, default=Path('/workplace/UKClimate/data/analysis/chq_building_only_v1/chq_building_only_scores.parquet'))
    ap.add_argument('--out', type=Path, default=Path('/workplace/UKClimate/data/analysis/chq_building_clusters_v1'))
    ap.add_argument('--site', type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    downloads = args.site/'downloads'
    protocol = {
        'model': 'CHQ_building_patterns_v1', 'seed': SEED, 'analysis_date': '2026-10-28',
        'features': FEATURES, 'encoding': 'Existing equally spaced ordinal 0, .25, .5, .75, 1; higher means better EPC rating.',
        'method': 'Weighted ordinary K-means on distinct observed six-attribute profiles; multiplicities exactly reproduce the full fitting cohort objective.',
        'distance': 'Squared Euclidean on the original 0–1 scores; six dimensions have equal explicit weights. No CHQ total, PCA, geography, year, price or weather is a clustering input.',
        'fit_cohort': 'All complete latest records, one per previously connected UPRN/EPC entity. Latest year, then source_row breaks ties. Descriptive pooled fit; no untouched-test or forecasting claim.',
        'missing_policy': 'All six ratings must be observed; no imputation. Incomplete records remain unassigned (-1).',
        'k_candidates': list(range(2, 11)), 'n_init': 30,
        'selection': {'rule': 'Smallest k within 0.02 silhouette of the best eligible k; eligibility requires every cluster >=2% of fitting homes and median LAD-bootstrap ARI >=0.80.',
                      'silhouette_tolerance': SIL_TOLERANCE, 'minimum_cluster_share': MIN_SHARE,
                      'minimum_bootstrap_median_ari': MIN_ARI,
                      'threshold_status': 'Exploratory researcher-set descriptive resolution tolerances, not preregistered rules or housing-quality standards.'},
        'silhouette_evaluation': 'Fixed random sample of 5,000 complete latest homes; multiplicities preserved. Used for descriptive k selection, not external validation.',
        'stability': '20 whole-LAD bootstrap reweightings for each k; re-fit K-means with 10 starts, evaluate ARI on the same fixed 5,000-home sample. ARI is permutation invariant. P10 is empirical, not a formal confidence bound.',
        'sensitivity': 'Refit same k after z-scoring dimensions; compare ARI, aligned centroids and shares. Also show fitted-pattern proportions by dwelling type, report type and latest transaction year.',
        'geography': 'Existing ONS 2024 LAD codes; pool one latest observation per entity. Annual maps are latest-record cohorts, not full annual transaction samples or within-home transitions.',
        'limitations': ['EPC attribute patterns are exploratory; no independent indoor thermal/health/climate outcome validation.',
                       'Six equally spaced ordinal ratings are a modelling assumption.',
                       'Clustering may reflect report method, dwelling mix and transaction year; subgroup proportions are descriptive, not adjusted effects.',
                       'A dominant area type is a plurality among classified sampled homes, not a label for every home or the population housing stock.',
                       'A nearest-centroid assignment does not establish natural or causal housing categories.']
    }
    dump(args.out/'analysis_protocol.json', protocol)
    d = pd.read_parquet(args.scores).reset_index(drop=True)
    assert d.source_row.is_unique
    assert d.loc[d.is_latest_entity, 'entity'].is_unique
    cols = ['s_'+v for v in FEATURES]
    a = d[cols].to_numpy(dtype=float)
    complete = np.isfinite(a).all(axis=1)
    latest = d.is_latest_entity.to_numpy(bool)
    fitting = latest & complete
    assert np.isin(a[complete], [0,.25,.5,.75,1]).all()
    assert np.allclose(d.loc[complete,'chq_building_only'], a[complete].mean(1)*100, atol=1e-5)
    x = a[fitting]
    u, inv, w = np.unique(x, axis=0, return_inverse=True, return_counts=True)
    rng = np.random.default_rng(SEED)
    eix = rng.choice(len(x), min(5000, len(x)), replace=False)
    ev = x[eix]
    # Counts of unique profiles per LAD permit exact block bootstrap reweighting.
    lad = d.loc[fitting,'onspd_lad_code'].fillna('unmapped').to_numpy(str)
    areas, acode = np.unique(lad, return_inverse=True)
    joint = np.zeros((len(areas), len(u)), dtype=np.int64)
    np.add.at(joint, (acode, inv), 1)
    brng = np.random.default_rng(SEED+100)
    multipliers = [np.bincount(brng.integers(0,len(areas),len(areas)),minlength=len(areas)) for _ in range(BOOTSTRAPS)]
    models = {}; metrics = []; stability = []
    log('fitting', len(x), 'homes;', len(u), 'distinct profiles;', len(areas), 'LAD groups incl. unmapped')
    for k in protocol['k_candidates']:
        m = fit(u, w, k)
        models[k] = m
        pred = m.predict(ev)
        shares = np.bincount(m.labels_, weights=w, minlength=k)/w.sum()
        aris = []
        for b, mult in enumerate(multipliers):
            bw = mult @ joint
            bm = fit(u, bw, k, SEED+1000+b, 10)
            ari = adjusted_rand_score(pred, bm.predict(ev))
            aris.append(ari)
            stability.append({'k':k,'replicate':b+1,'ari':ari})
        row = {'k':k,'inertia':m.inertia_, 'silhouette':silhouette_score(ev,pred),
               'calinski_harabasz':calinski_harabasz_score(ev,pred),
               'davies_bouldin':davies_bouldin_score(ev,pred),
               'min_cluster_share':float(shares.min()), 'bootstrap_ari_median':float(np.median(aris)),
               'bootstrap_ari_p10':float(np.quantile(aris,.10))}
        row['eligible'] = row['min_cluster_share'] >= MIN_SHARE and row['bootstrap_ari_median'] >= MIN_ARI
        metrics.append(row)
        log(row)
    grid = pd.DataFrame(metrics)
    eligible = grid[grid.eligible]
    if eligible.empty:
        grid.to_csv(args.out/'k_diagnostics.csv',index=False)
        raise RuntimeError('No k meets the protocol stability and size thresholds; do not invent a primary solution.')
    best = eligible.silhouette.max()
    k = int(eligible.loc[eligible.silhouette.ge(best-SIL_TOLERANCE),'k'].min())
    grid['selected'] = grid.k.eq(k)
    grid.to_csv(args.out/'k_diagnostics.csv',index=False)
    pd.DataFrame(stability).to_csv(args.out/'bootstrap_stability.csv',index=False)
    dump(args.out/'candidate_centers.json', {str(kk):mm.cluster_centers_.tolist() for kk,mm in models.items()})
    model = models[k]
    # Canonical IDs from descending mean building quality (IDs themselves are nominal).
    order = np.argsort(-model.cluster_centers_.mean(axis=1))
    remap = np.empty(k,dtype=int);remap[order] = np.arange(k)
    centers = model.cluster_centers_[order]
    memberships = np.full(len(d), -1, dtype=np.int16)
    memberships[complete] = remap[model.predict(a[complete])]
    d['cluster_id'] = memberships
    clustered = d.loc[fitting].copy()
    clustered['chq'] = a[fitting].mean(1)*100
    profiles = []
    for i in range(k):
        ix = clustered.cluster_id.eq(i)
        rows = clustered.loc[ix]
        values = a[fitting][ix].mean(axis=0)*100
        profiles.append({'cluster_id':i, 'name':'Pattern '+str(i+1), 'name_zh':'模式'+str(i+1),
                         'color':COLORS[i % len(COLORS)], 'n':int(ix.sum()),
                         'share':float(ix.mean()),'chq':float(rows.chq.mean()),
                         'chq_sd':float(rows.chq.std()),
                         'chq_p10':float(rows.chq.quantile(.1)), 'chq_p90':float(rows.chq.quantile(.9)),
                         **{label:float(v) for label,v in zip(LABELS,values)}})
    # Interpret the centroids only after fitting. Names describe ratings, not actual outcomes.
    if k == 4:
        # Match the four expected attribute combinations to data, rather than arbitrary numeric labels.
        names = {
            'high': ('Stronger envelope and services', '围护与设备较优型'),
            'walls': ('Weak walls, stronger services', '墙体短板、设备较好型'),
            'light': ('Lighting shortfall', '照明短板型'),
            'services': ('Heating and hot-water shortfall', '采暖与热水短板型')}
        high = int(np.argmax(centers.mean(axis=1)))
        services = int(np.argmin(centers[:,[2,4]].mean(axis=1)))
        light = int(np.argmin(centers[:,5]))
        wall = int(np.argmin(centers[:,0]))
        assert len(set([high,services,light,wall])) == 4
        for index,key in [(high,'high'),(wall,'walls'),(light,'light'),(services,'services')]:
            profiles[index]['name'], profiles[index]['name_zh'] = names[key]
    profile_df = pd.DataFrame(profiles)
    profile_df.to_csv(args.out/'cluster_profiles.csv',index=False)
    # z-score sensitivity uses the full fitting distribution but keeps fixed k.
    mu = np.average(u,axis=0,weights=w)
    sd = np.sqrt(np.average((u-mu)**2,axis=0,weights=w))
    zm = fit((u-mu)/sd, w, k, SEED+200)
    zpred = zm.predict((ev-mu)/sd)
    base_pred = remap[model.predict(ev)]
    contingency = np.zeros((k,k),dtype=np.int64)
    np.add.at(contingency,(remap[model.labels_],zm.labels_),w)
    ri,ci = linear_sum_assignment(-contingency)
    zcenters = zm.cluster_centers_*sd+mu
    sensitivity = {'standardised_ari_on_evaluation_sample':float(adjusted_rand_score(base_pred,zpred)),
                   'standardised_aligned_population_agreement':float(contingency[ri,ci].sum()/w.sum()),
                   'standardised_matched_centers_0_100':{str(int(i)):(zcenters[j]*100).tolist() for i,j in zip(ri,ci)},
                   'note':'Sensitivity to metric choice, not a reason to tune primary labels after observing results.'}
    report_sensitivity = []
    for report_type, part in clustered.groupby('report_type', dropna=False):
        if len(part) < 10000:
            continue
        xx = part[cols].to_numpy(float)
        uu, ww = np.unique(xx, axis=0, return_counts=True)
        stratified_model = fit(uu, ww, k, SEED+300)
        test_x = xx[np.random.default_rng(SEED+301).choice(len(xx), min(5000,len(xx)),replace=False)]
        sg_pred = stratified_model.predict(test_x)
        global_pred = remap[model.predict(test_x)]
        record = {'report_type':str(report_type), 'n':len(xx),
                  'ari_global_vs_within_report_type':float(adjusted_rand_score(global_pred,sg_pred)),
                  'silhouette_within_report_type':float(silhouette_score(test_x,sg_pred)),
                  'within_report_type_centers_0_100':(stratified_model.cluster_centers_*100).tolist(),
                  'within_report_type_cluster_shares':(np.bincount(stratified_model.labels_,weights=ww,minlength=k)/ww.sum()).tolist(),
                  'global_pattern_shares':(np.bincount(remap[model.predict(uu)],weights=ww,minlength=k)/ww.sum()).tolist()}
        report_sensitivity.append(record)
    sensitivity['within_report_type_refits'] = report_sensitivity
    dump(args.out/'sensitivity.json',sensitivity)
    subgroup = []
    for field in ['property_type','report_type','transaction_year_clean']:
        tab = pd.crosstab(clustered[field].fillna('Unknown'),clustered.cluster_id)
        for group,r in tab.iterrows():
            for i in range(k):
                subgroup.append({'group_variable':field,'group':str(group),'cluster_id':i,'n':int(r.get(i,0)),
                                 'total_classified':int(r.sum()),'share':float(r.get(i,0)/r.sum())})
    pd.DataFrame(subgroup).to_csv(args.out/'subgroup_shares.csv',index=False)
    # One stable universe of areas and names, as on the established atlas.
    text = (args.site/'assets/map-data.js').read_text()
    atlas = json.JSONDecoder().raw_decode(text.split('const DATA=',1)[1])[0]
    names = {c:{'name':r['name'],'region':r['region']} for c,r in atlas['all'].items()}
    mapdata = {}; summary_rows = []
    latest_rows = d.loc[latest]
    periods = ['all'] + [str(y) for y in sorted(d.transaction_year_clean.unique())]
    for period in periods:
        frame = latest_rows if period == 'all' else latest_rows[latest_rows.transaction_year_clean.eq(int(period))]
        total = frame.groupby('onspd_lad_code',dropna=False).size()
        valid = frame[frame.cluster_id.ge(0)]
        grouped = valid.groupby('onspd_lad_code').agg(n=('cluster_id','size'),chq=('chq_building_only','mean'))
        counts = pd.crosstab(valid.onspd_lad_code,valid.cluster_id)
        mapdata[period] = {}
        for code,info in names.items():
            n_total = int(total.get(code,0))
            n = int(grouped.loc[code,'n']) if code in grouped.index else 0
            cs = [int(counts.loc[code,i]) if code in counts.index and i in counts else 0 for i in range(k)]
            ties = np.flatnonzero(np.asarray(cs) == max(cs)) if n else []
            dominant = int(ties[0]) if n else None
            obj = {**info, 'total':n_total,'n':n,'counts':cs,'shares':[v/n if n else 0 for v in cs],
                   'dominant':dominant, 'tied':len(ties)>1,
                   'chq':float(grouped.loc[code,'chq']) if n else None}
            mapdata[period][code] = obj
            for i in range(k):
                summary_rows.append({'period':period,'onspd_lad_code':code,**info,'cluster_id':i,
                                     'cluster_name':profiles[i]['name'],'n_cluster':cs[i], 'n_classified':n,
                                     'total_latest_entities':n_total,'cluster_share':cs[i]/n if n else None,
                                     'dominant_cluster_id':dominant,'dominant_tied':obj['tied']})
    pd.DataFrame(summary_rows).to_csv(args.out/'lad_cluster_shares.csv',index=False)
    # Source-level assignments remain local; no addresses or identifiers enter the site.
    keep = ['source_row','entity','is_latest_entity','onspd_lad_code','transaction_year_clean',
            'property_type','report_type','chq_building_only','cluster_id']
    d[keep].to_parquet(args.out/'cluster_assignments.parquet',index=False,compression='zstd')
    exact = remap[model.predict(a[fitting])]
    assert np.array_equal(exact,memberships[fitting])
    assert (memberships[~complete] == -1).all()
    assert sum(p['n'] for p in profiles) == int(fitting.sum())
    assert np.allclose(profile_df[LABELS].mean(axis=1),profile_df.chq,atol=1e-5)
    mapped = d.onspd_lad_code.isin(names).to_numpy() & fitting
    assert sum(r['n'] for r in mapdata['all'].values()) == int(mapped.sum())
    assert all(sum(mapdata[p][c]['n'] for p in periods[1:]) == r['n'] for c,r in mapdata['all'].items())
    assert all(sum(r['counts']) == r['n'] for per in mapdata.values() for r in per.values())
    # Independent sample distance check against saved centers.
    check = rng.choice(np.flatnonzero(fitting),10000,replace=False)
    distances = ((a[check,None,:]-centers[None,:,:])**2).sum(axis=2)
    assert np.allclose(distances[np.arange(len(check)),memberships[check]],distances.min(axis=1),atol=1e-10)
    summary = {
        'selected_k':k, 'fit_entities_total':int(latest.sum()),'fit_entities_complete':int(fitting.sum()),
        'fit_entities_excluded':int((latest&~complete).sum()),'source_transactions':len(d),
        'classified_source_transactions':int(complete.sum()), 'mapped_fit_entities':int(mapped.sum()),
        'distinct_fit_profiles':len(u), 'evaluation_sample':len(ev),
        'selected_diagnostics':grid.loc[grid.k.eq(k)].iloc[0].to_dict(),
        'sensitivity':sensitivity,'profiles':profiles,
        'fit_centers_0_1':centers.tolist(),
        'fit_sha256':hashlib.sha256(args.scores.read_bytes()).hexdigest(),
        'classification_formula':'Assign to the nearest saved six-dimensional centroid in squared Euclidean distance. Missing any feature => unassigned.',
        'checks':'passed: entity uniqueness, exact ordinal coding, unchanged baseline score, assigned counts, annual/pooled aggregation, nearest centroid and profile-score consistency.'}
    dump(args.out/'model_summary.json',summary)
    dump(args.out/'verification.json',{'status':'passed','checks':summary['checks']})
    for filename,public in [('cluster_profiles.csv','chq_building_cluster_profiles.csv'),
                            ('k_diagnostics.csv','chq_building_cluster_diagnostics.csv'),
                            ('bootstrap_stability.csv','chq_building_cluster_stability.csv'),
                            ('subgroup_shares.csv','chq_building_cluster_subgroups.csv'),
                            ('lad_cluster_shares.csv','chq_building_cluster_lad_shares.csv')]:
        (downloads/public).write_bytes((args.out/filename).read_bytes())
    dump(downloads/'chq_building_cluster_model.json',{'protocol':protocol,'results':summary})
    web = {'features':FEATURES,'labels':LABELS,'profiles':profiles,'summary':{key:summary[key] for key in ['selected_k','fit_entities_total','fit_entities_complete','fit_entities_excluded','mapped_fit_entities','selected_diagnostics','sensitivity']},'periods':mapdata}
    (args.site/'assets/building-clusters.js').write_text('const BUILDING_CLUSTERS='+json.dumps(web,separators=(',',':'),ensure_ascii=False,allow_nan=False)+';\n')
    log('SELECTED',k,'clusters; sensitivity ARI',sensitivity['standardised_ari_on_evaluation_sample'])
    print(profile_df.to_string(index=False),flush=True)
    plots(args,profile_df,grid)


def plots(args,profiles,grid):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax = plt.subplots(figsize=(11,4.5),layout='constrained')
    im=ax.imshow(profiles[LABELS],cmap='YlGnBu',vmin=0,vmax=100,aspect='auto')
    ax.set_xticks(range(6),LABELS)
    ax.set_yticks(range(len(profiles)),[f"{r.name}\n{r.share:.1%} · CHQ {r.chq:.1f}" for r in profiles.itertuples(index=False)])
    for i,r in enumerate(profiles[LABELS].to_numpy()):
        for j,v in enumerate(r):ax.text(j,i,f'{v:.1f}',ha='center',va='center',color='white' if v>64 else '#172e42',fontsize=12)
    ax.set_title('Building-only CHQ patterns: mean observed EPC attribute ratings',pad=14)
    fig.colorbar(im,ax=ax,label='Mean rating (0–100)')
    for ext in ['png','pdf']:
        fig.savefig(args.out/f'cluster_profiles.{ext}',dpi=200)
        (args.site/'downloads'/f'chq_building_cluster_profiles.{ext}').write_bytes((args.out/f'cluster_profiles.{ext}').read_bytes())
    plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(12,3.4),layout='constrained')
    for ax,key,title in zip(axs,['inertia','silhouette','bootstrap_ari_median'],['Within-cluster sum of squares','Silhouette (5,000 homes)','Median LAD-bootstrap ARI']):
        ax.plot(grid.k,grid[key],'-o',color='#216e6a')
        ax.axvline(int(grid.loc[grid.selected,'k'].iloc[0]),ls='--',color='#cc8132',label='Selected k')
        ax.set(xlabel='Clusters (k)',title=title);ax.spines[['top','right']].set_visible(False)
    fig.savefig(args.out/'cluster_diagnostics.png',dpi=200)
    (args.site/'downloads/chq_building_cluster_diagnostics.png').write_bytes((args.out/'cluster_diagnostics.png').read_bytes())
    plt.close(fig)

if __name__ == '__main__':
    main()
