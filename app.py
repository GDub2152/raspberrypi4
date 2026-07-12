from flask import Flask, jsonify, render_template, request
from pathlib import Path
import json, time, urllib.request, urllib.parse

APP_DIR = Path(__file__).parent
CONFIG_FILE = APP_DIR / 'config.json'
app = Flask(__name__)

def load_config():
    return json.loads(CONFIG_FILE.read_text())

def save_config(data):
    CONFIG_FILE.write_text(json.dumps(data, indent=2))

def fetch_json(url, timeout=8):
    req = urllib.request.Request(url, headers={'User-Agent':'PiSportsScoreboard/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))

@app.get('/')
def dashboard():
    return render_template('index.html')

@app.get('/settings')
def settings():
    return render_template('settings.html')

@app.get('/api/config')
def get_config():
    return jsonify(load_config())

@app.post('/api/config')
def update_config():
    current = load_config()
    incoming = request.get_json(force=True) or {}
    for key in current:
        if key in incoming:
            current[key] = incoming[key]
    save_config(current)
    return jsonify({'ok': True, 'config': current})

@app.get('/api/weather')
def weather():
    c = load_config()
    q = urllib.parse.urlencode({
        'latitude': c['latitude'], 'longitude': c['longitude'],
        'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,surface_pressure',
        'temperature_unit': 'fahrenheit', 'wind_speed_unit': 'mph',
        'timezone': c.get('timezone','America/New_York')
    })
    try:
        return jsonify(fetch_json('https://api.open-meteo.com/v1/forecast?' + q))
    except Exception as e:
        return jsonify({'error': str(e)}), 502

SPORT_PATHS = {
    'mlb':'baseball/mlb', 'nfl':'football/nfl', 'nba':'basketball/nba',
    'nhl':'hockey/nhl', 'ncaaf':'football/college-football',
    'ncaam':'basketball/mens-college-basketball', 'wnba':'basketball/wnba'
}

@app.get('/api/scores/<sport>')
def scores(sport):
    path = SPORT_PATHS.get(sport)
    if not path: return jsonify({'error':'unsupported sport'}), 404
    try:
        data = fetch_json(f'https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard')
        games=[]
        for ev in data.get('events',[]): 
            comp=(ev.get('competitions') or [{}])[0]
            teams=[]
            for x in comp.get('competitors',[]):
                t=x.get('team',{})
                teams.append({'name':t.get('shortDisplayName') or t.get('abbreviation'),'abbr':t.get('abbreviation'),'score':x.get('score','0'),'logo':t.get('logo'),'winner':x.get('winner',False),'homeAway':x.get('homeAway')})
            games.append({'name':ev.get('shortName'), 'status':comp.get('status',{}).get('type',{}).get('shortDetail',''), 'teams':teams, 'date':ev.get('date')})
        return jsonify({'sport':sport,'games':games,'updated':int(time.time())})
    except Exception as e:
        return jsonify({'sport':sport,'games':[],'error':str(e)}), 502

@app.get('/api/solar')
def solar():
    out={'updated':int(time.time())}
    try:
        kp=fetch_json('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json')
        if len(kp)>1: out['kp']=kp[-1][1]
    except Exception as e: out['kp_error']=str(e)
    try:
        flux=fetch_json('https://services.swpc.noaa.gov/json/solar-cycle/f10-7cm-flux.json')
        if flux: out['solar_flux']=flux[-1].get('flux') or flux[-1].get('f10.7')
    except Exception as e: out['flux_error']=str(e)
    try:
        wind=fetch_json('https://services.swpc.noaa.gov/products/solar-wind/plasma-5-minute.json')
        if len(wind)>1: out['solar_wind']=wind[-1][2]
    except Exception as e: out['wind_error']=str(e)
    return jsonify(out)

@app.get('/api/adsb')
def adsb():
    c=load_config(); base=c.get('adsb_url','http://127.0.0.1/tar1090/data/aircraft.json').rstrip('/')
    urls=[base]
    if not base.endswith('.json'):
        urls += [base+'/data/aircraft.json', base+'/tar1090/data/aircraft.json']
    last='not configured'
    for url in urls:
        try:
            d=fetch_json(url,4); ac=d.get('aircraft',[])
            visible=[a for a in ac if a.get('seen',999)<60]
            nearest=sorted(visible,key=lambda a:a.get('r_dst',99999))[:6]
            return jsonify({'count':len(visible),'aircraft':nearest,'source':url,'now':d.get('now')})
        except Exception as e: last=str(e)
    return jsonify({'count':0,'aircraft':[],'error':last}), 502

@app.get('/api/headlines')
def headlines():
    c=load_config(); items=[]
    for sport in c.get('sports',['mlb','nfl','nhl']):
        path=SPORT_PATHS.get(sport)
        if not path: continue
        try:
            d=fetch_json(f'https://site.api.espn.com/apis/site/v2/sports/{path}/news?limit=5')
            for a in d.get('articles',[])[:3]: items.append(a.get('headline'))
        except Exception: pass
    return jsonify({'headlines':[x for x in items if x][:12]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
