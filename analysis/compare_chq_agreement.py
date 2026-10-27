#!/usr/bin/env python3
"""Descriptive agreement of published CHQ variants; publish aggregates only."""
import argparse
import hashlib
import json
import os
from itertools import combinations
from pathlib import Path
import time

os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.metrics import cohen_kappa_score, normalized_mutual_info_score

MODELS = [
    {'id':'41','label':'41-variable baseline','short':'41 equal','column':'baseline41'},
    {'id':'5','label':'5-variable candidate','short':'5 candidate','column':'candidate5'},
    {'id':'10','label':'10-variable candidate','short':'10 candidate','column':'candidate10'},
    {'id':'18','label':'18-variable candidate','short':'18 candidate','column':'candidate18'},
    {'id':'building','label':'Building-only · 6 attributes','short':'Building 6','column':'building6'},
    {'id':'pca41','label':'41-variable PCA · 4 PCs','short':'41 PCA','column':'pca41'},
]
COLS = [m['column'] for m in MODELS]
IDS = [m['id'] for m in MODELS]


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def plain(x):
    if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [plain(v) for v in x]
    if isinstance(x,np.generic):return plain(x.item())
    if isinstance(x,float) and not np.isfinite(x):return None
    return x


def dump(path,obj):
    path.write_text(json.dumps(plain(obj),indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def ranks(x):
    # Average ranks preserve ties. Do not split equal scores into arbitrary categories.
    r=np.column_stack([rankdata(x[:,j],method='average') for j in range(x.shape[1])])
    p=(r-.5)/len(x)
    q=np.minimum(4,np.floor(p*5)).astype('int8')
    low=np.quantile(x,.1,axis=0); high=np.quantile(x,.9,axis=0)
    return r,p,q,low,high


def pair_stats(a,b,ra,rb,pa,pb,qa,qb,lo_a,lo_b,hi_a,hi_b):
    n=len(a)
    va,vb=np.var(a),np.var(b)
    cov=np.mean((a-a.mean())*(b-b.mean()))
    delta=b-a
    bottom_a=a<=lo_a;bottom_b=b<=lo_b
    top_a=a>=hi_a;top_b=b>=hi_b
    result={
        'n':n,'pearson':np.corrcoef(a,b)[0,1], 'spearman':np.corrcoef(ra,rb)[0,1],
        'ccc':2*cov/(va+vb+(a.mean()-b.mean())**2),
        'kappa':cohen_kappa_score(qa,qb,labels=[0,1,2,3,4],weights='quadratic'),
        'same_quintile':np.mean(qa==qb),
        'bottom_jaccard':np.sum(bottom_a&bottom_b)/np.sum(bottom_a|bottom_b),
        'top_jaccard':np.sum(top_a&top_b)/np.sum(top_a|top_b),
        'mean_a':a.mean(),'mean_b':b.mean(),'mean_difference_b_minus_a':delta.mean(),
        'mae':np.mean(np.abs(delta)), 'rmse':np.sqrt(np.mean(delta**2)),
        'difference_sd':np.std(delta,ddof=1),
        'difference_p025':np.quantile(delta,.025),'difference_p975':np.quantile(delta,.975),
        'mean_abs_percentile_gap':100*np.mean(np.abs(pa-pb)),
        'bottom_cutoff_a':lo_a,'bottom_cutoff_b':lo_b,
        'top_cutoff_a':hi_a,'top_cutoff_b':hi_b,
        'bottom_share_a':bottom_a.mean(),'bottom_share_b':bottom_b.mean(),
        'top_share_a':top_a.mean(),'top_share_b':top_b.mean(),
    }
    return plain(result)


def compute_all(x,scope):
    assert np.isfinite(x).all()
    r,p,q,lo,hi=ranks(x)
    out=[]
    for i,j in combinations(range(6),2):
        row={'scope':scope,'a':IDS[i],'b':IDS[j],**pair_stats(x[:,i],x[:,j],r[:,i],r[:,j],p[:,i],p[:,j],q[:,i],q[:,j],lo[i],lo[j],hi[i],hi[j])}
        out.append(row)
    # Kendall's W with ties; general rank concordance across all six published scores.
    m=x.shape[1];n=len(x)
    S=np.sum((r.sum(axis=1)-m*(n+1)/2)**2)
    tie_sum=0.
    for j in range(m):
        counts=np.unique(x[:,j],return_counts=True)[1].astype(float)
        tie_sum+=np.sum(counts**3-counts)
    W=12*S/(m*m*(float(n)**3-n)-m*tie_sum)
    return out,float(W),q


def read_aligned(path,columns,source):
    d=pd.read_parquet(path,columns=['source_row']+columns)
    assert np.array_equal(d.source_row.to_numpy(),source),str(path)+' source-row mismatch'
    return d


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=Path('/workplace/UKClimate/data/analysis'))
    ap.add_argument('--out',type=Path,default=Path('/workplace/UKClimate/data/analysis/chq_agreement_v1'))
    ap.add_argument('--site',type=Path,default=Path(__file__).resolve().parents[1])
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    src=args.root/'chq_building_only_v1/chq_building_only_scores.parquet'
    d=pd.read_parquet(src,columns=['source_row','entity','is_latest_entity','chq_building_only','transaction_year_clean','onspd_lad_code','property_type','report_type'])
    source=d.source_row.to_numpy();assert d.source_row.is_unique
    assert d.loc[d.is_latest_entity,'entity'].is_unique
    inp={
        'baseline':args.root/'chq_equal_variables_v1/chq_scores.parquet',
        'candidates':args.root/'chq_selection_v1/chq_selected_scores.parquet',
        'building':src,
        'pca':args.root/'chq_pca41_v1/chq_pca41_scores.parquet',
        'patterns':args.root/'chq_building_clusters_v1/cluster_assignments.parquet'}
    d['baseline41']=read_aligned(inp['baseline'],['chq_equal'],source).chq_equal.to_numpy(float)
    selected=read_aligned(inp['candidates'],['chq_5','chq_10','chq_18'],source)
    for k in [5,10,18]:d[f'candidate{k}']=selected[f'chq_{k}'].to_numpy(float)
    d['building6']=d.chq_building_only.to_numpy(float)
    d['pca41']=read_aligned(inp['pca'],['chq_pca41'],source).chq_pca41.to_numpy(float)
    d['cluster_id']=read_aligned(inp['patterns'],['cluster_id'],source).cluster_id.to_numpy(int)
    values=d[COLS].to_numpy(float)
    finite=np.isfinite(values)
    assert np.all((values[finite]>=0)&(values[finite]<=100))
    latest=d.is_latest_entity.to_numpy(bool)
    common=finite.all(axis=1)&latest
    transactions=finite.all(axis=1)
    assert (d.loc[common,'cluster_id']>=0).all()
    home=d.loc[latest].copy();df=d.loc[common].copy()
    log('latest',latest.sum(),'common homes',len(df),'common transactions',transactions.sum())
    coverage=[]
    for i,model in enumerate(MODELS):
        coverage.append({'model':model['id'],'label':model['label'],
                         'latest_available':int((finite[:,i]&latest).sum()),'latest_total':int(latest.sum()),
                         'latest_coverage':float(finite[latest,i].mean()),
                         'transaction_available':int(finite[:,i].sum()),'transaction_total':len(d),
                         'transaction_coverage':float(finite[:,i].mean())})
    primary,W,q=compute_all(values[common],'common_homes')
    log('common rank W',W)
    pairwise=[]
    for i,j in combinations(range(6),2):
        valid=latest&finite[:,i]&finite[:,j]
        x=values[valid][:,[i,j]]
        r,p,qq,lo,hi=ranks(x)
        pairwise.append({'scope':'pairwise_homes','a':IDS[i],'b':IDS[j],**pair_stats(x[:,0],x[:,1],r[:,0],r[:,1],p[:,0],p[:,1],qq[:,0],qq[:,1],lo[0],lo[1],hi[0],hi[1])})
        log('pairwise',IDS[i],IDS[j],len(x))
    trans,transW,_=compute_all(values[transactions],'common_transactions')
    # Means of the same complete homes inside each authority. Equal weight per LAD.
    atlastext=(args.site/'assets/map-data.js').read_text()
    atlas=json.JSONDecoder().raw_decode(atlastext.split('const DATA=',1)[1])[0]
    area_names={code:{'name':r['name'],'region':r['region']} for code,r in atlas['all'].items()}
    mapped=df[df.onspd_lad_code.isin(area_names)]
    grouped=mapped.groupby('onspd_lad_code').agg(n=('source_row','size'),**{c:(c,'mean') for c in COLS}).reset_index()
    grouped['name']=grouped.onspd_lad_code.map({c:r['name'] for c,r in area_names.items()})
    grouped['region']=grouped.onspd_lad_code.map({c:r['region'] for c,r in area_names.items()})
    grouped['eligible']=grouped.n.ge(100)
    eligible=grouped[grouped.eligible].copy()
    for c in COLS:eligible[c+'_rank']=rankdata(-eligible[c],method='average')
    area_pairs,areaW,_=compute_all(eligible[COLS].to_numpy(float),'common_authorities')
    areas=[{'code':r['onspd_lad_code'],'name':r['name'],'region':r['region'],'n':int(r['n']),
            'scores':{m['id']:float(r[m['column']]) for m in MODELS},
            'ranks':{m['id']:float(r[m['column']+'_rank']) for m in MODELS}} for _,r in eligible.iterrows()]
    grouped.to_csv(args.out/'authority_means.csv',index=False)
    eligible.to_csv(args.out/'authority_ranks.csv',index=False)
    # Descriptive same-common-cohort subgroup correlations against the 41-variable baseline.
    subgroups=[];cohort_groups=[]
    for field in ['report_type','property_type','transaction_year_clean']:
        for group,g in home.groupby(field,dropna=False):
            good=np.isfinite(g[COLS]).all(axis=1)
            cohort_groups.append({'group_variable':field,'group':str(group),'n_latest':len(g),
                                  'n_common':int(good.sum()),'common_coverage':float(good.mean())})
        for group,g in df.groupby(field,dropna=False):
            if len(g)<100:continue
            x=g[COLS].to_numpy(float)
            r=np.column_stack([rankdata(x[:,i]) for i in range(6)])
            cor=np.corrcoef(r,rowvar=False)
            for i,j in combinations(range(6),2):
                subgroups.append({'group_variable':field,'group':str(group),'n_common':len(g),
                                  'a':IDS[i],'b':IDS[j],'spearman':cor[i,j]})
    # Patterns are nominal. Compare score distributions and eta-squared/NMI, never correlate their IDs.
    patinfo=json.loads((args.site/'downloads/chq_building_cluster_model.json').read_text())['results']['profiles']
    patterns=[];association=[]
    for j,m in enumerate(MODELS):
        x=df[m['column']].to_numpy(float);labels=df.cluster_id.to_numpy()
        grand=x.mean();total=np.sum((x-grand)**2);between=0.
        for k,part in df.groupby('cluster_id'):
            v=part[m['column']].to_numpy(float)
            between+=len(v)*(v.mean()-grand)**2
            patterns.append({'cluster_id':int(k),'pattern':patinfo[int(k)]['name'],'model':m['id'],
                             'n':len(v),'share_common':len(v)/len(df),'mean':float(v.mean()),'sd':float(v.std(ddof=1)),
                             'p10':float(np.quantile(v,.1)),'median':float(np.median(v)),'p90':float(np.quantile(v,.9))})
        association.append({'model':m['id'],'eta_squared':float(between/total),
                            'nmi_with_score_rank_quintile':float(normalized_mutual_info_score(labels,q[:,j]))})
    # Coverage comparison helps identify complete-case selection.
    common_coverage=len(df)/int(latest.sum())
    diagnostics={
        'date':'2026-10-28','models':MODELS,'source_transactions':len(d),
        'latest_homes':int(latest.sum()),'common_homes':len(df),'common_home_coverage':common_coverage,
        'common_transactions':int(transactions.sum()),'mapped_common_homes':len(mapped),
        'eligible_authorities':len(eligible),'eligible_authority_homes':int(eligible.n.sum()),
        'authority_minimum_common_homes':100,
        'kendall_w_common_homes':W,'kendall_w_common_authorities':areaW,'kendall_w_common_transactions':transW,
        'coverage':coverage, 'pattern_associations':association,
        'primary_sample':'One latest record per connected UPRN/EPC entity; all six published scores finite. No imputation, refit or weights added.',
        'pairwise_sample':'One latest record per entity; both selected scores finite. Denominators differ between pairs.',
        'area_sample':'Equal-weight authority means of identical all-six-complete homes, minimum 100 per authority. Area-level consistency does not imply household-level consistency.',
        'tie_policy':'Spearman uses average ranks; quintiles use floor(5*(average_rank-.5)/n), clipped to 0..4, keeping equal scores together. Threshold-inclusive bottom <= empirical P10 and top >= empirical P90; groups may exceed 10% because of ties. Actual tail fractions accompany every pair.',
        'metric_definitions':{
            'spearman':'Pearson correlation of average ranks; ranking association, not absolute score agreement.',
            'pearson':'Linear score correlation; does not establish equal scores.',
            'ccc':'Lin concordance correlation = 2 cov(A,B)/(var(A)+var(B)+(mean(A)-mean(B))^2); population moments. Measures numerical agreement on the published 0–100 scales.',
            'kappa':'Quadratic-weighted Cohen kappa for within-cohort rank quintiles, fixed labels 0..4.',
            'bottom_jaccard':'Intersection / union of threshold-inclusive bottom-decile sets.',
            'top_jaccard':'Intersection / union of threshold-inclusive top-decile sets.',
            'mean_difference_b_minus_a':'Mean(score B - score A); raw published points, direction depends on selected order.',
            'mae':'Mean absolute paired score difference, in published score points.',
            'rmse':'Root mean squared paired score difference, in published score points.',
            'mean_abs_percentile_gap':'Mean absolute difference of average-rank percentiles, in percentage points.',
            'kendall_w':'Tie-corrected Kendall concordance W across all six ranking systems.',
            'eta_squared':'Between-pattern sum of squares / total score sum of squares. Unadjusted nominal-pattern association, not validity or agreement.',
            'nmi_with_score_rank_quintile':'Permutation-invariant normalized mutual information of nominal patterns and score-rank quintiles; descriptive association only.'},
        'limitations':[
            'Shared EPC inputs create structural dependence; high agreement is not independent climate or health validation.',
            '41 baseline uses original full-sample coding; 5/10/18 candidates use discovery-frozen coding. Comparisons use published scores as-is, not harmonized refits.',
            'PCA uses its published percentile rescaling and median-imputed inputs; its score units have different calibration. Low CCC can coexist with high rank correlation.',
            'All-six complete-case restriction selects a subset; compare pairwise coverage and dwelling/report/year diagnostics.',
            'The PCA composite sign was aligned to the equal-weight baseline during its construction; positive association was partly built in.',
            'Quintiles and tails are empirical relative groups, not clinical thresholds. Ties are retained, without arbitrary equal-size splitting.',
            'Cluster IDs are nominal. Pattern-score eta-squared and NMI describe association and reuse six core inputs, not causal effects or independent validation.',
            'No confidence intervals or causal claims; results describe this dataset. The pooled latest-year cohorts are not a longitudinal panel.'],
        'source_files':{key:str(v.relative_to(args.root)) for key,v in inp.items()},
        'source_sha256':{key:hashlib.sha256(v.read_bytes()).hexdigest() for key,v in inp.items()}
    }
    pairs=primary+pairwise+area_pairs+trans
    pd.DataFrame(pairs).to_csv(args.out/'pair_metrics.csv',index=False)
    pd.DataFrame(coverage).to_csv(args.out/'model_coverage.csv',index=False)
    pd.DataFrame(subgroups).to_csv(args.out/'subgroup_rank_correlations.csv',index=False)
    pd.DataFrame(cohort_groups).to_csv(args.out/'common_cohort_coverage.csv',index=False)
    pd.DataFrame(patterns).to_csv(args.out/'pattern_score_distributions.csv',index=False)
    pd.DataFrame(association).to_csv(args.out/'pattern_associations.csv',index=False)
    dump(args.out/'method_and_summary.json',diagnostics)
    for scope in [primary,pairwise,area_pairs,trans]:
        assert len(scope)==15
        for row in scope:
            for key in ['pearson','spearman','ccc','kappa']:
                assert row[key] is not None and -1.000001<=row[key]<=1.000001
            for key in ['same_quintile','bottom_jaccard','top_jaccard']:
                assert 0<=row[key]<=1
    assert all(p['n']==len(df) for p in primary)
    assert sum(p['n'] for p in patterns if p['model']=='41')==len(df)
    assert len(mapped)==int(grouped.n.sum())
    assert len(df)==2694335
    # Independent APIs for one pair verify vectorized ranks, concordance direction and quintiles.
    check=primary[0]
    assert np.isclose(check['spearman'],spearmanr(df.baseline41,df.candidate5).statistic)
    assert np.isclose(check['mean_difference_b_minus_a'],(df.candidate5-df.baseline41).mean())
    assert check['n']==len(df)
    dump(args.out/'verification.json',{'status':'passed','checks':['Aligned unique source rows across five source files','Unique latest entities','Common cohort and mapped counts reconcile','15 pairs per scope with correct denominators','All metric ranges','Pattern-score cohort reconciliation','Independent Spearman and bias checks'],'common_homes':len(df)})
    # Copy published aggregates; source-level scores/identifiers remain on server.
    names={'pair_metrics.csv':'chq_agreement_pairs.csv','model_coverage.csv':'chq_agreement_coverage.csv',
           'authority_ranks.csv':'chq_agreement_authorities.csv','subgroup_rank_correlations.csv':'chq_agreement_subgroups.csv',
           'common_cohort_coverage.csv':'chq_agreement_common_coverage.csv','pattern_score_distributions.csv':'chq_agreement_patterns.csv',
           'pattern_associations.csv':'chq_agreement_pattern_associations.csv','method_and_summary.json':'chq_agreement_methods.json'}
    for local,public in names.items():(args.site/'downloads'/public).write_bytes((args.out/local).read_bytes())
    web={'models':MODELS,'summary':{key:diagnostics[key] for key in ['latest_homes','common_homes','common_home_coverage','eligible_authorities','eligible_authority_homes','kendall_w_common_homes','kendall_w_common_authorities']},
         'coverage':coverage,'common_cohort_coverage':cohort_groups,'pairs':primary+pairwise+area_pairs,'authorities':areas,'pattern_distributions':patterns,
         'pattern_associations':association,'pattern_names':[p['name'] for p in patinfo]}
    (args.site/'assets/agreement-data.js').write_text('const CHQ_AGREEMENT='+json.dumps(plain(web),separators=(',',':'),ensure_ascii=False,allow_nan=False)+';\n')
    report(args,diagnostics,primary,area_pairs,pairwise,patterns)
    log('done',diagnostics['common_homes'],'common homes;',len(eligible),'authorities')
    for p in primary:
        if p['a']=='41':log('baseline vs',p['b'],'rho',p['spearman'],'CCC',p['ccc'],'low J',p['bottom_jaccard'],'high J',p['top_jaccard'])


def report(args,summary,primary,areas,pairwise,patterns):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    labels=[m['short'] for m in MODELS]
    fig,axs=plt.subplots(1,2,figsize=(12,5.5),layout='constrained')
    for ax,key,title in zip(axs,['spearman','ccc'],['Rank association · Spearman rho','Numerical agreement · Lin CCC']):
        mat=np.eye(6)
        for p in primary:
            i,j=IDS.index(p['a']),IDS.index(p['b']);mat[i,j]=mat[j,i]=p[key]
        im=ax.imshow(mat,cmap='BrBG',vmin=-1,vmax=1)
        ax.set_xticks(range(6),labels,rotation=45,ha='right');ax.set_yticks(range(6),labels)
        ax.set_title(title)
        for i in range(6):
            for j in range(6):ax.text(j,i,f'{mat[i,j]:.2f}',ha='center',va='center',color='white' if abs(mat[i,j])>.6 else '#17313a')
    fig.colorbar(im,ax=axs,label='Coefficient',shrink=.8)
    fig.suptitle(f'Same {summary["common_homes"]:,} latest sampled homes · six published CHQ scores')
    fig.savefig(args.out/'agreement_heatmaps.png',dpi=180)
    fig.savefig(args.out/'agreement_heatmaps.pdf')
    plt.close(fig)
    for ext in ['png','pdf']:(args.site/'downloads'/f'chq_agreement_heatmaps.{ext}').write_bytes((args.out/f'agreement_heatmaps.{ext}').read_bytes())
    rows=['# Agreement of published CHQ scores','','Analysis date: 28 October 2026.','',
          '## Cohort and fair comparison','',
          f'The primary comparison uses **{summary["common_homes"]:,} latest sampled homes** with all six published scores available, out of {summary["latest_homes"]:,} latest homes ({summary["common_home_coverage"]:.1%}). Each connected UPRN/EPC entity contributes its latest transaction-year record, breaking ties by source_row. Published scores are joined by exact source-row alignment and are not refitted or imputed for this analysis.','',
          'Scores: original 41-variable available-score baseline; discovery-frozen complete 5-, 10- and 18-variable candidates; complete six-attribute building-only score; and the published 41-variable / four-PC composite. Candidate text/scaling coding differs from the original baseline. The PCA has different percentile-based calibration and imputation. Agreement describes these published definitions, not harmonized reimplementations.','',
          f'Secondary results include pairwise-available latest homes, all-six-complete transactions (n = {summary["common_transactions"]:,}), and **{summary["eligible_authorities"]} authority means** based on identical complete homes with at least 100 such homes per authority. Every authority has equal weight. Aggregation may raise correlations; area results cannot substitute for household agreement.','',
          '## Main household results against the 41-variable baseline','','| Other score | Spearman rho | Pearson r | Lin CCC | Weighted quintile kappa | Bottom-decile Jaccard | Top-decile Jaccard | Mean B - baseline | MAE |',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    lookup={m['id']:m['label'] for m in MODELS}
    for p in primary:
        if p['a']!='41':continue
        rows.append('| '+lookup[p['b']]+' | '+' | '.join(f"{p[k]:.3f}" for k in ['spearman','pearson','ccc','kappa','bottom_jaccard','top_jaccard','mean_difference_b_minus_a','mae'])+' |')
    rows+=['','## The common cohort is selective','',
           '**All 2,694,335 common homes are report type 2; no report-type-3 homes satisfy all six score definitions.** Only 1.35% of flats and 6.26% of maisonettes remain in the common cohort, versus 83.21% of houses and 96.38% of bungalows. This primary matrix is internally comparable but is not representative of all housing or all EPC report types. Pairwise results are essential sensitivity checks.','',
           '| Other score versus 41 baseline | Pairwise latest homes | Spearman rho | Lin CCC |','|---|---:|---:|---:|']
    for p in pairwise:
        if p['a']=='41':rows.append(f"| {lookup[p['b']]} | {p['n']:,} | {p['spearman']:.3f} | {p['ccc']:.3f} |")
    rows+=['',f'Tie-corrected Kendall concordance W across all six rank systems is **{summary["kendall_w_common_homes"]:.4f}** for common homes and **{summary["kendall_w_common_authorities"]:.4f}** for eligible common-cohort authorities. These summarize concordance, not validity.','',
           '## Interpreting the metrics','',
           '- Spearman rho: alignment of average ranks. Pearson r: linear association. Neither establishes identical numerical scores.',
           '- Lin CCC: `2 cov(A,B)/(var(A)+var(B)+(mean(A)-mean(B))²)` using population moments. It penalizes scale and location differences. Reported on published 0–100 scales; PCA rescaling changes the interpretation.',
           '- Quadratic-weighted Cohen kappa: agreement of within-cohort rank quintiles. Average ranks keep ties intact; quintile = `min(4,floor(5*(average_rank-.5)/n))`. Equal-score homes are never split arbitrarily, so group sizes can differ.',
           '- Bottom/top decile Jaccard: intersection divided by union for `score <= empirical P10` and `score >= empirical P90`. Threshold ties are included; effective tail fractions can exceed 10%. Cutoffs and actual fractions are in pair downloads and the website details.',
           '- Mean difference is B minus A in published score points. MAE and RMSE describe paired numerical differences; average absolute percentile gaps describe ranking shifts.',
           '- No confidence intervals, p-values or causal claims are reported; this is a descriptive comparison of the linked dataset.','',
           '## Patterns are nominal','',
           'The four building patterns are not seventh numeric scores. They are compared using score distributions within each pattern, eta-squared (between-pattern / total score variation), and normalized mutual information with score-rank quintiles. These are associations, not agreement, ranking of type IDs or validation. All such comparisons use the same six-score-complete home cohort.','',
           '## Coverage and subgroup sensitivity','',
           'Use `chq_agreement_coverage.csv` for per-model availability, `chq_agreement_common_coverage.csv` for common-cohort retention by report type, dwelling type and latest transaction year, and `chq_agreement_subgroups.csv` for same-common-cohort pairwise rank correlations within those groups. Pairwise sample results in `chq_agreement_pairs.csv` use different denominators per score pair; compare them with the fixed common-cohort primary results. The website displays both.','',
           '## Limits','']
    rows+=['- '+s for s in summary['limitations']]
    rows+=['','## Reproduction and verification','','```bash','python3 analysis/compare_chq_agreement.py --root /path/to/analysis --out /path/to/local/agreement','```','',
           'Dependencies: numpy, pandas, pyarrow, scipy, scikit-learn and matplotlib. Only aggregate CSV/JSON/figures are published. No dwelling identifiers or source-level scores are uploaded. The methods JSON records metric definitions, source paths and SHA256 checksums. Validation checks aligned rows, entity uniqueness, counts, metric ranges, pattern totals, source-geography reconciliation and independent Spearman/bias calculations.']
    text='\n'.join(rows)+'\n'
    (args.out/'report.md').write_text(text)
    (args.site/'downloads/chq_agreement_report.md').write_text(text)

if __name__=='__main__':main()
