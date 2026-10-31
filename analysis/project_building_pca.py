#!/usr/bin/env python3
"""Project the existing six-attribute building clusters onto two PCA axes.

Fit uses all complete latest homes with original 0..1 scales, mean-centred only,
matching the metric of the existing K-means. Frequency-weighted covariance of
unique profiles equals full-home covariance; class labels are not refitted.
Only aggregate rating-profile coordinates and figures enter the public site.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

FEATURES=['walls_energy_eff','windows_energy_eff','mainheat_energy_eff',
          'mainheatc_energy_eff','hot_water_energy_eff','lighting_energy_eff']
LABELS=['Walls','Windows','Main heating','Heating controls','Hot water','Lighting']


def write_json(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=Path('/workplace/UKClimate/data/analysis'))
    ap.add_argument('--out',type=Path,default=Path('/workplace/UKClimate/data/analysis/chq_building_pca2_v1'))
    ap.add_argument('--site',type=Path,default=Path(__file__).resolve().parents[1])
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    d=pd.read_parquet(args.root/'chq_building_only_v1/chq_building_only_scores.parquet',
                      columns=['source_row','entity','is_latest_entity']+['s_'+v for v in FEATURES])
    labels=pd.read_parquet(args.root/'chq_building_clusters_v1/cluster_assignments.parquet',columns=['source_row','cluster_id'])
    assert d.source_row.equals(labels.source_row)
    x=d[['s_'+v for v in FEATURES]].to_numpy(float)
    ok=d.is_latest_entity.to_numpy(bool)&np.isfinite(x).all(axis=1)
    assert d.loc[ok,'entity'].is_unique
    x=x[ok];cluster=labels.loc[ok,'cluster_id'].to_numpy(int)
    assert (cluster>=0).all()
    u,inv,w=np.unique(x,axis=0,return_inverse=True,return_counts=True)
    cluster_counts=np.zeros((len(u),4),dtype=np.int64)
    np.add.at(cluster_counts,(inv,cluster),1)
    # A six-rating profile maps to one fixed cluster; preserve exact existing labels.
    assert (np.count_nonzero(cluster_counts,axis=1)==1).all()
    uc=cluster_counts.argmax(axis=1)
    n=int(w.sum())
    mean=np.average(u,weights=w,axis=0)
    centered=u-mean
    cov=(centered.T*w)@centered/(n-1)
    eigenvalues,eigenvectors=np.linalg.eigh(cov)
    order=np.argsort(-eigenvalues);eig=eigenvalues[order];vectors=eigenvectors[:,order]
    # Choose a reproducible sign: largest absolute coefficient is positive.
    for i in range(6):
        j=np.abs(vectors[:,i]).argmax()
        if vectors[j,i]<0:vectors[:,i]*=-1
    ratio=eig/eig.sum()
    pcs=centered@vectors
    correlation_loadings=vectors*np.sqrt(eig)[None,:]/np.sqrt(np.diag(cov))[:,None]
    profiles=pd.read_csv(args.site/'downloads/chq_building_cluster_profiles.csv')
    profile_rows=[]
    for i in range(len(u)):
        profile_rows.append({'profile_id':i,'cluster_id':int(uc[i]),'n_homes':int(w[i]),
                             'share':float(w[i]/n),'pc1':float(pcs[i,0]),'pc2':float(pcs[i,1]),
                             **{f:float(u[i,j]) for j,f in enumerate(FEATURES)}})
    pd.DataFrame(profile_rows).to_csv(args.out/'profile_coordinates.csv',index=False)
    var=pd.DataFrame({'component':range(1,7),'eigenvalue':eig,'explained_variance_ratio':ratio,
                      'cumulative':np.cumsum(ratio)})
    var.to_csv(args.out/'explained_variance.csv',index=False)
    load=pd.DataFrame({'variable':FEATURES,'label':LABELS,'mean_input':mean,
                       'PC1_coefficient':vectors[:,0],'PC2_coefficient':vectors[:,1],
                       'PC1_correlation_loading':correlation_loadings[:,0],
                       'PC2_correlation_loading':correlation_loadings[:,1]})
    load.to_csv(args.out/'loadings.csv',index=False)
    centers=[]
    for i,r in profiles.iterrows():
        sel=uc==r.cluster_id
        center=np.average(pcs[sel,:2],weights=w[sel],axis=0)
        centers.append({'cluster_id':int(r.cluster_id),'name':r['name'],'name_zh':r.name_zh,
                        'color':r.color,'n':int(w[sel].sum()),'share':float(w[sel].sum()/n),
                        'pc1':float(center[0]),'pc2':float(center[1])})
    # Population density histogram uses exact household frequencies, not number of unique profiles.
    xedges=np.linspace(pcs[:,0].min(),pcs[:,0].max(),91)
    yedges=np.linspace(pcs[:,1].min(),pcs[:,1].max(),71)
    counts=np.zeros((90,70,4),dtype=np.int64)
    ix=np.clip(np.searchsorted(xedges,pcs[:,0],side='right')-1,0,89)
    iy=np.clip(np.searchsorted(yedges,pcs[:,1],side='right')-1,0,69)
    np.add.at(counts,(ix,iy,uc),w)
    bins=[{'x':float((xedges[i]+xedges[i+1])/2),'y':float((yedges[j]+yedges[j+1])/2),
           'counts':[int(v) for v in counts[i,j]],'n':int(counts[i,j].sum())}
          for i,j in zip(*np.where(counts.sum(axis=2)>0))]
    # Keep full per-home coordinates locally for further research; do not publish identifiers.
    local=pd.DataFrame({'source_row':d.loc[ok,'source_row'].to_numpy(),
                        'cluster_id':cluster,'pc1':pcs[inv,0].astype('float32'),
                        'pc2':pcs[inv,1].astype('float32')})
    local.to_parquet(args.out/'latest_home_pca_coordinates.parquet',index=False,compression='zstd')
    # Exact mathematical checks, independent covariance and original-centre projections.
    assert n==3978388 and len(u)==7507
    assert np.allclose(vectors.T@vectors,np.eye(6),atol=1e-12)
    assert np.allclose(cov,np.cov(x,rowvar=False),atol=1e-12)
    assert np.allclose(np.average(pcs,weights=w,axis=0),0,atol=1e-12)
    assert np.allclose((pcs.T*w)@pcs/(n-1),np.diag(eig),atol=1e-12)
    assert sum(b['n'] for b in bins)==n
    assert np.array_equal(np.sum([b['counts'] for b in bins],axis=0),profiles.n)
    for c in centers:
        original=profiles.loc[profiles.cluster_id.eq(c['cluster_id']),LABELS].to_numpy()[0]/100
        assert np.allclose((original-mean)@vectors[:,:2],[c['pc1'],c['pc2']],atol=1e-12)
    rng=np.random.default_rng(20261031)
    check=rng.choice(n,2000,replace=False)
    assert np.allclose(local.iloc[check][['pc1','pc2']],(x[check]-mean)@vectors[:,:2],atol=1e-7)
    spec={
        'model':'CHQ_building_PCA2_v1','analysis_date':'2026-10-31',
        'input_features':FEATURES,'n_homes':n,'n_unique_profiles':len(u),
        'fit_cohort':'Same complete latest-record homes used for the four existing building-only clusters. One home per previously connected entity, no missing-value imputation.',
        'method':'Covariance PCA on original 0–1 ordinal scores. Mean-centred, not z-score standardized, to match the existing K-means metric. Exact frequency-weighted covariance of all distinct profiles.',
        'center':mean.tolist(),'component_coefficients':vectors.T.tolist(),
        'eigenvalues':eig.tolist(),'explained_variance_ratio':ratio.tolist(),
        'PC1_PC2_cumulative_variance':float(ratio[:2].sum()),
        'sign_convention':'For each component, its coefficient with largest absolute value is oriented positive; PCA signs carry no intrinsic meaning.',
        'formula':'PC_k = sum_j ((x_j - fitted mean_j) * component_coefficient[k,j]).',
        'labels':'Four existing six-dimensional K-means labels retained; PCA is for visualization only. No reclustering in two dimensions.',
        'display':'All 7,507 distinct profiles plotted without random sampling or jitter, weighted by their home frequency. Overlapping records share coordinates. A profile marker is not one home. Density bins use exact home counts.',
        'density':{'x_bins':90,'y_bins':70,'cell_width':float(xedges[1]-xedges[0]),'cell_height':float(yedges[1]-yedges[0]),'opacity':'log(1 + cell count) / log(1 + maximum displayed cell count); colour is the most frequent existing pattern in the cell.'},
        'centroids':centers,
        'limits':['The two axes discard the remaining variance. Visual overlap in PC1/PC2 does not invalidate or confirm six-dimensional cluster separation.',
                  'PCA axes are linear combinations of ordinal EPC scores, not physical temperature or a new CHQ score.',
                  'Projection uses the original clustering scale; z-score PCA would give different axes and variance shares.',
                  'The clusters and projection reuse the same inputs; this is an exploratory visualization, not independent climate/health validation.',
                  'The plot is pooled across latest-year cohorts and is independent of map area/year controls.']}
    write_json(args.out/'model_specification.json',spec)
    write_json(args.out/'verification.json',{'status':'passed','n_homes':n,'profiles':len(u),
               'checks':['Original labels retained','Entity uniqueness and complete cohort','Weighted covariance equals all-home covariance','Orthonormal eigenvectors and diagonal PC covariance','Zero weighted PC means','All density counts and cluster totals reconcile','PCA centroids equal transformed original cluster means','Independent sampled per-home transform']})
    payload={'summary':{'n_homes':n,'n_profiles':len(u),'variance':ratio.tolist(),'retained':float(ratio[:2].sum())},
             'labels':LABELS,'features':FEATURES,'loadings':load.to_dict('records'),'clusters':centers,
             'profiles':[[float(pcs[i,0]),float(pcs[i,1]),int(uc[i]),int(w[i]),*[float(z) for z in u[i]]] for i in range(len(u))],
             'bounds':[float(pcs[:,0].min()),float(pcs[:,0].max()),float(pcs[:,1].min()),float(pcs[:,1].max())],
             'bins':bins,'cell_width':spec['density']['cell_width'],'cell_height':spec['density']['cell_height']}
    (args.site/'assets/building-pca2-data.js').write_text('const BUILDING_PCA2='+json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False)+';\n')
    for name,public in [('profile_coordinates.csv','chq_building_pca2_profiles.csv'),('explained_variance.csv','chq_building_pca2_variance.csv'),('loadings.csv','chq_building_pca2_loadings.csv'),('model_specification.json','chq_building_pca2_model.json')]:
        (args.site/'downloads'/public).write_bytes((args.out/name).read_bytes())
    plots(args,payload,pcs,w,uc)
    print(json.dumps({'homes':n,'profiles':len(u),'explained_variance':ratio.tolist(),'PC1_PC2_cumulative':spec['PC1_PC2_cumulative_variance'],'coefficients':load.to_dict('records')},indent=2),flush=True)


def plots(args,data,pcs,w,labels):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgb
    fig,axs=plt.subplots(1,2,figsize=(13,6),layout='constrained',sharex=True,sharey=True)
    colors=[c['color'] for c in data['clusters']]
    for k,c in enumerate(data['clusters']):
        ix=labels==k
        axs[0].scatter(pcs[ix,0],pcs[ix,1],s=4+32*np.log1p(w[ix])/np.log1p(w.max()),c=c['color'],alpha=.30,edgecolors='none',rasterized=True)
    axs[0].set_title('Rating profiles · marker size follows log home count\nColour = existing cluster; crosses = projected means')
    from matplotlib.patches import Rectangle
    mx=max(b['n'] for b in data['bins'])
    for b in data['bins']:
        k=int(np.argmax(b['counts']));alpha=.15+.85*np.log1p(b['n'])/np.log1p(mx)
        axs[1].add_patch(Rectangle((b['x']-data['cell_width']/2,b['y']-data['cell_height']/2),data['cell_width'],data['cell_height'],facecolor=colors[k],alpha=alpha,lw=0,rasterized=True))
    axs[1].set_title('All-home density · log count intensity\nColour = plurality cluster in each bin')
    for ax in axs:
        for i,c in enumerate(data['clusters']):
            ax.scatter(c['pc1'],c['pc2'],marker='X',s=120,c=c['color'],edgecolors='white',lw=1.1,zorder=10)
            ax.annotate(str(i+1),(c['pc1'],c['pc2']),xytext=(8,7),textcoords='offset points',weight='bold',fontsize=10)
        ax.axhline(0,color='#abb8bb',lw=.6,zorder=-1);ax.axvline(0,color='#abb8bb',lw=.6,zorder=-1)
        ax.set_xlabel(f"PC1 ({data['summary']['variance'][0]:.2%} variance)")
        ax.set_aspect('equal',adjustable='box');ax.spines[['top','right']].set_visible(False)
        ax.set_xlim(data['bounds'][0]-.06,data['bounds'][1]+.06);ax.set_ylim(data['bounds'][2]-.06,data['bounds'][3]+.06)
    axs[0].set_ylabel(f"PC2 ({data['summary']['variance'][1]:.2%} variance)")
    from matplotlib.lines import Line2D
    handles=[Line2D([0],[0],marker='o',color='none',markerfacecolor=c['color'],markersize=8,label=f"{i+1}. {c['name']} ({c['share']:.1%})") for i,c in enumerate(data['clusters'])]
    fig.legend(handles=handles,loc='outside lower center',ncol=2,frameon=False,fontsize=9)
    fig.suptitle(f"Building-only CHQ: six attributes projected onto PC1 / PC2\n{data['summary']['n_homes']:,} latest homes · {data['summary']['n_profiles']:,} unique profiles · cumulative variance {data['summary']['retained']:.2%}",fontsize=13)
    for ext in ['png','pdf']:
        fig.savefig(args.out/f'building_pca2.{ext}',dpi=200)
        (args.site/'downloads'/f'chq_building_pca2.{ext}').write_bytes((args.out/f'building_pca2.{ext}').read_bytes())
    plt.close(fig)

if __name__=='__main__':main()
