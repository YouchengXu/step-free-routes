# Step-Free Routes

I&E Team 14 app prototype: step-free wheelchair routing through Soho, London.

Live: https://candfire.com/step-free-routes/

Rebuild the map after editing `template.html`:

```
python build_map.py soho.osm          # writes mapdata.json
python -c "open('index.html','w',encoding='utf-8').write(open('template.html',encoding='utf-8').read().replace('/*MAPDATA*/',open('mapdata.json',encoding='utf-8').read()))"
```
