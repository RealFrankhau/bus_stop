import urllib.request, json, time
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f'Error fetching {url}: {e}', flush=True)
        return None

def fetch_kmb_stops():
    print('Fetching KMB/LWB stops...', flush=True)
    data = fetch_json('https://data.etabus.gov.hk/v1/transport/kmb/stop')
    if not data:
        print('Failed to fetch KMB stops', flush=True)
        return {}
    
    stops = {}
    for stop in data['data']:
        sid = stop['stop']
        stops[sid] = {
            'stop_id': sid,
            'lat': float(stop['lat']),
            'lng': float(stop['long']),
            'name': stop.get('name_tc', ''),
            'companies': {},
            'source': 'kmb'
        }
    print(f'Fetched {len(stops)} KMB/LWB stops', flush=True)
    return stops

def fetch_kmb_route_stops():
    print('Fetching KMB/LWB route-stop list...', flush=True)
    data = fetch_json('https://data.etabus.gov.hk/v1/transport/kmb/route-stop')
    if not data:
        print('Failed to fetch KMB route-stop list', flush=True)
        return {}
    
    stop_routes = {}
    for item in data.get('data', []):
        sid = item['stop']
        route = item['route']
        if sid not in stop_routes:
            stop_routes[sid] = []
        if route not in stop_routes[sid]:
            stop_routes[sid].append(route)
    
    print(f'Processed {len(stop_routes)} stops with routes', flush=True)
    return stop_routes

def fetch_td_route_classification():
    print('Fetching TD route classification...', flush=True)
    url = 'https://static.data.gov.hk/td/routes-fares-xml/ROUTE_BUS.xml'
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=60) as resp:
            content = resp.read().decode('utf-8')
    except Exception as e:
        print(f'Failed to fetch TD routes: {e}', flush=True)
        return {}
    
    route_company = {}
    import re
    routes = re.findall(r'<ROUTE>(.*?)</ROUTE>', content, re.DOTALL)
    for route in routes:
        route_id = re.search(r'<ROUTE_ID>(.*?)</ROUTE_ID>', route)
        company = re.search(r'<COMPANY_CODE>(.*?)</COMPANY_CODE>', route)
        route_name = re.search(r'<ROUTE_NAMEC>(.*?)</ROUTE_NAMEC>', route)
        if route_id and company and route_name:
            rid = route_id.group(1)
            co = company.group(1)
            name = route_name.group(1)
            route_company[name] = co
    
    print(f'Classified {len(route_company)} routes', flush=True)
    return route_company

def fetch_ctb_routes():
    print('Fetching CTB routes...', flush=True)
    data = fetch_json('https://rt.data.gov.hk/v2/transport/citybus/route/ctb')
    if not data:
        print('Failed to fetch CTB routes', flush=True)
        return []
    
    routes = data['data'] or []
    unique_routes = []
    seen = set()
    for r in routes:
        key = r['route']
        if key not in seen:
            seen.add(key)
            unique_routes.append(r)
    
    print(f'Fetched {len(unique_routes)} unique CTB routes', flush=True)
    return unique_routes

def fetch_ctb_route_stops(route, direction):
    url = f'https://rt.data.gov.hk/v2/transport/citybus/route-stop/ctb/{route}/{direction}'
    data = fetch_json(url)
    if not data or not data.get('data'):
        return []
    return data['data']

def fetch_ctb_stop_detail(stop_id):
    url = f'https://rt.data.gov.hk/v1/transport/citybus-nwfb/stop/{stop_id}'
    data = fetch_json(url)
    if not data or not data.get('data'):
        return None
    return data['data']

def fetch_all_ctb_stops():
    print('Fetching CTB stops...', flush=True)
    routes = fetch_ctb_routes()
    if not routes:
        return {}
    
    print('Collecting CTB stop IDs from routes...', flush=True)
    unique_stop_ids = set()
    stop_routes = {}
    route_count = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for route in routes:
            for direction in ['inbound', 'outbound']:
                futures.append(executor.submit(fetch_ctb_route_stops, route['route'], direction))
        
        for future in as_completed(futures):
            result = future.result()
            for stop in result:
                sid = stop['stop']
                unique_stop_ids.add(sid)
                if sid not in stop_routes:
                    stop_routes[sid] = []
                route_num = stop['route']
                if route_num not in stop_routes[sid]:
                    stop_routes[sid].append(route_num)
            route_count += 1
            if route_count % 50 == 0:
                print(f'  Processed {route_count} route-directions, found {len(unique_stop_ids)} unique stops', flush=True)
    
    print(f'Total unique CTB stops: {len(unique_stop_ids)}', flush=True)
    
    print('Fetching CTB stop details...', flush=True)
    stops = {}
    stop_ids = list(unique_stop_ids)
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}
        for stop_id in stop_ids:
            futures[executor.submit(fetch_ctb_stop_detail, stop_id)] = stop_id
        
        completed = 0
        for future in as_completed(futures):
            stop_id = futures[future]
            detail = future.result()
            if detail and detail.get('lat') and detail.get('long'):
                routes = stop_routes.get(stop_id, [])
                stops[stop_id] = {
                    'stop_id': stop_id,
                    'lat': float(detail['lat']),
                    'lng': float(detail['long']),
                    'name': detail.get('name_tc', ''),
                    'companies': {'CTB': sorted(routes)},
                    'source': 'ctb'
                }
            completed += 1
            if completed % 100 == 0:
                print(f'  Fetched details for {completed}/{len(stop_ids)} stops', flush=True)
    
    print(f'Successfully fetched {len(stops)} CTB stop details', flush=True)
    return stops

def main():
    start_time = time.time()
    
    # Fetch TD route classification
    route_company = fetch_td_route_classification()
    
    # Fetch KMB/LWB stops
    kmb_stops = fetch_kmb_stops()
    
    # Fetch KMB route-stop list and build route mapping
    kmb_stop_routes = fetch_kmb_route_stops()
    
    # Assign routes to KMB/LWB stops using TD classification
    for sid, stop in kmb_stops.items():
        routes = kmb_stop_routes.get(sid, [])
        kmb_routes = []
        lwb_routes = []
        for route in routes:
            co = route_company.get(route, '')
            if co == 'LWB':
                lwb_routes.append(route)
            else:
                kmb_routes.append(route)
        
        stop['companies'] = {}
        if kmb_routes:
            stop['companies']['KMB'] = sorted(kmb_routes)
        if lwb_routes:
            stop['companies']['LWB'] = sorted(lwb_routes)
        
        if not stop['companies']:
            stop['companies']['KMB'] = []
    
    # Fetch CTB stops
    ctb_stops = fetch_all_ctb_stops()
    
    # Combine all stops
    all_stops = {}
    
    for sid, stop in kmb_stops.items():
        all_stops[sid] = stop
    
    for sid, stop in ctb_stops.items():
        all_stops[sid] = stop
    
    # Group stops by GPS coordinates
    print('\nGrouping stops by GPS coordinates...', flush=True)
    from collections import defaultdict
    location_groups = defaultdict(list)
    
    for sid, stop in all_stops.items():
        key = (stop['lat'], stop['lng'])
        location_groups[key].append(stop)
    
    # Create location-based stops
    output = []
    for (lat, lng), stops in location_groups.items():
        if len(stops) == 1:
            output.append(stops[0])
        else:
            output.append({
                'stop_id': stops[0]['stop_id'],
                'lat': lat,
                'lng': lng,
                'name': stops[0]['name'],
                'companies': stops[0]['companies'],
                'source': stops[0]['source'],
                'stops': stops
            })
    
    print(f'Total locations: {len(output)}', flush=True)
    print(f'Locations with multiple stops: {sum(1 for s in output if "stops" in s)}', flush=True)
    
    with open('bus_stops.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)
    
    elapsed = time.time() - start_time
    print(f'\nSaved bus_stops.json in {elapsed:.1f} seconds', flush=True)

if __name__ == '__main__':
    main()
