import xml.etree.ElementTree as ET, math, json, heapq, collections, sys
src=sys.argv[1]
root=ET.parse(src).getroot()
LAT0,LON0=51.5185,-0.1445
K=math.cos(math.radians(51.5145))*111320
def proj(lat,lon): return ((lon-LON0)*K, (LAT0-lat)*110540)
nodes={}
for n in root.iter('node'): nodes[n.get('id')]=proj(float(n.get('lat')),float(n.get('lon')))
ways=[]
for w in root.iter('way'):
    tags={t.get('k'):t.get('v') for t in w.iter('tag')}
    refs=[r.get('ref') for r in w.iter('nd') if r.get('ref') in nodes]
    if len(refs)>1: ways.append((tags,refs))
def pd(refs,close=False):
    s='M'+' L'.join(f"{nodes[r][0]:.1f} {nodes[r][1]:.1f}" for r in refs)
    return s+('Z' if close else '')
bld=[];park=[];roads=collections.defaultdict(list)
MAJOR={'primary','secondary','tertiary','trunk'};MINOR={'residential','unclassified','living_street','pedestrian'}
for tags,refs in ways:
    if 'building' in tags and refs[0]==refs[-1]: bld.append(pd(refs,True))
    elif tags.get('leisure') in('park','garden') or tags.get('landuse')=='grass':
        if refs[0]==refs[-1]: park.append(pd(refs,True))
    hw=tags.get('highway')
    if hw:
        if hw in MAJOR: roads['major'].append(pd(refs))
        elif hw in MINOR or hw=='service': roads['minor' if hw!='service' else 'service'].append(pd(refs))
        elif hw in('footway','path','steps','cycleway'):
            if tags.get('footway') in('sidewalk','crossing'): continue
            roads['foot'].append(pd(refs))
# graph
OK=MAJOR|MINOR|{'pedestrian'}
G=collections.defaultdict(list)
for tags,refs in ways:
    hw=tags.get('highway')
    if hw not in OK or tags.get('access')=='private': continue
    name=tags.get('name','')
    for a,b in zip(refs,refs[1:]):
        d=math.dist(nodes[a],nodes[b]); G[a].append((b,d,name)); G[b].append((a,d,name))
def near(lat,lon):
    p=proj(lat,lon); return min(G,key=lambda n:math.dist(nodes[n],p))
def sp(s,t,avoid=(),pen=None):
    dist={s:0};prev={};pq=[(0,s)]
    while pq:
        d,u=heapq.heappop(pq)
        if u==t: break
        if d>dist[u]: continue
        for v,w,name in G[u]:
            if name in avoid: continue
            if pen and name in pen: w*=pen[name]
            nd=d+w
            if nd<dist.get(v,1e18): dist[v]=nd;prev[v]=u;heapq.heappush(pq,(nd,v))
    path=[t]
    while path[-1]!=s: path.append(prev[path[-1]])
    return path[::-1]
def names(path):
    out=[]
    for a,b in zip(path,path[1:]):
        nm=next((n for v,w,n in G[a] if v==b),'')
        if not out or out[-1][0]!=nm: out.append([nm,0])
        out[-1][1]+=math.dist(nodes[a],nodes[b])
    return [(n,round(l)) for n,l in out]
S=near(51.51628,-0.13088); T=near(51.51398,-0.14000)
pol=[n for n in G if any(x=='Poland Street' for _,_,x in G[n]) and any(x=='Oxford Street' for _,_,x in G[n])]
print('poland/oxford nodes',pol)
A=sp(S,pol[0])+sp(pol[0],T)[1:]
B=sp(S,T,pen={'Oxford Street':6})
print('A',names(A)); print('B',names(B))
json.dump({'nodes':{k:nodes[k] for k in set(A+B)},'A':A,'B':B,'S':S,'T':T},open('routes_dbg.json','w'))
import pickle; pickle.dump((nodes,dict(G),ways),open('g.pkl','wb'))
# labels
lab={}
for tags,refs in ways:
    hw=tags.get('highway');nm=tags.get('name')
    if not nm or hw not in MAJOR|MINOR: continue
    L=sum(math.dist(nodes[a],nodes[b]) for a,b in zip(refs,refs[1:]))
    if L>lab.get(nm,(0,))[0]:
        # longest segment
        a,b=max(zip(refs,refs[1:]),key=lambda p:math.dist(nodes[p[0]],nodes[p[1]]))
        (x1,y1),(x2,y2)=nodes[a],nodes[b]
        ang=math.degrees(math.atan2(y2-y1,x2-x1))
        if ang>90: ang-=180
        if ang<-90: ang+=180
        lab[nm]=(L,round((x1+x2)/2,1),round((y1+y2)/2,1),round(ang,1),hw in MAJOR,round(math.dist((x1,y1),(x2,y2))))
xs=[p[0] for p in nodes.values()];ys=[p[1] for p in nodes.values()]
out={'w':round(1070),'h':round(890),'bld':''.join(bld),'park':''.join(park),'roads':{k:''.join(v) for k,v in roads.items()},
 'labels':[[n,v[1],v[2],v[3],v[4]] for n,v in lab.items() if v[0]>60 and v[5]>22]}
json.dump(out,open('mapdata.json','w'))
print(len(bld),len(park),{k:len(v) for k,v in roads.items()},len(out['labels']),'bytes',len(json.dumps(out)))
def junc(a,b):
    J=[n for n in G if any(x==a for _,_,x in G[n]) and any(x==b for _,_,x in G[n])]
    if J: return J
    na=[n for n in G if any(x==a for _,_,x in G[n])]; nb=[n for n in G if any(x==b for _,_,x in G[n])]
    if not na or not nb: return []
    return [min(na,key=lambda n:min(math.dist(nodes[n],nodes[m]) for m in nb))]
dean=junc('Oxford Street','Dean Street')[0]; ward=junc('Oxford Street','Wardour Street')[0]
B=sp(S,dean)+sp(dean,T,pen={'Oxford Street':8})[1:]
R=sp(ward,T,avoid={'Poland Street'})
print('B',names(B)); print('R',names(R))
def L(p): return round(sum(math.dist(nodes[a],nodes[b]) for a,b in zip(p,p[1:])))
print('len',L(A),L(B),L(R), 'A to ward', L(sp(S,ward)))
# hazards
kerb=junc('Great Chapel Street','Hollen Street')
pol_mid=[n for n in A if any(x=='Poland Street' for _,_,x in G[n])]
deanmid=sorted([n for n in G if any(x=='Dean Street' for _,_,x in G[n])],key=lambda n:nodes[n][1])
pts=lambda p:[[round(nodes[n][0],1),round(nodes[n][1],1)] for n in p]
out['routes']={'a':pts(A),'b':pts(B),'re':pts(R),'ward':pts([ward])[0]}
out['steps']={'a':names(A),'b':names(B),'re':names(R)}
print('B',names(B),'R',names(R));out['hz']={'kerb':pts(kerb[:1])[0],'car':pts(deanmid[len(deanmid)//3:len(deanmid)//3+1])[0],'block':pts(pol_mid[len(pol_mid)//2:len(pol_mid)//2+1])[0]}
json.dump(out,open('mapdata.json','w'))
print(out['hz'],out['routes']['a'][0],out['routes']['a'][-1])
