import asyncio
import aiohttp
import sys
import json
import time
import re

routes = {
        "Goloman": ["Hands", "Holiday", "Wilkes"],
        "Hands": ["Goloman", "Wilkes"],
        "Holiday": ["Goloman", "Wilkes", "Welsh"],
        "Wilkes": ["Goloman", "Hands", "Holiday"],
        "Welsh": ["Holiday"]
}

ports = {
        "Goloman": 12759,
        "Hands": 12760,
        "Holiday": 12761,
        "Wilkes": 12762,
        "Welsh": 12763
}

endpoint = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
api_key = ''

locations = {}


async def whats_at(loc, radius, results_limit):
    async with aiohttp.ClientSession() as session:
        modified_loc = re.sub("([0-9])([+-])", r"\1,\2", loc)
        modified_loc = re.sub("[+]", "", modified_loc)
        params = {'key': api_key, 'location': modified_loc, 'radius': int(radius) * 1000}
        async with session.get(endpoint,params=params) as http_resp:
            obj_resp = await http_resp.json()
            if len(obj_resp['results']) > results_limit:
                del obj_resp['results'][results_limit:]
            return json.dumps(obj_resp, indent=3)


async def flood(location):
    print('Flooding')
    for route in routes:
        try:
            reader, writer = await asyncio.open_connection(
                '127.0.0.1', ports[route])

            log.write("Connected to " + route + "\n")
            writer.write(location.encode())
            await writer.drain()
            writer.close()
            log.write("Closed connection to " + route + "\n")
        except ConnectionError:
                log.write("Error: Connection error to " + route + "\n")
                log.flush()


def validate_query(query):
    try:
        if query[0] == "IAMAT":
            loc = re.sub("([0-9])([+-])", r"\1,\2", query[2]).split(",")
            if len(loc) == 2 and float(loc[0]) and float(loc[1]):
                return True
            else:
                return False
        else:
            return False
    except ValueError:
        return False


async def handle_echo(reader, writer):
    try:
        data = await reader.read()
        rx_time = time.time()
        message = data.decode()
        query = message.split()
        if query[0] == "AT":
            if query[2] != server_name and (query[4] not in locations or query[5] > locations[query[4]].split()[5]):
                locations[query[4]] = message
                await flood(message)
        else:
            log.write("Query: " + message + "\n")
            if len(query) != 4 or not (query[0] == "IAMAT" or query[0] == "WHATSAT"):
                response = "? " + message
            elif query[0] == "IAMAT":
                if validate_query(query):
                    time_diff = rx_time - float(query[3])
                    time_str = str(time_diff)
                    if time_diff > 0:
                        time_str = "+" + time_str
                    response = "AT " + server_name + " " + time_str + " " + " ".join(query)
                    locations[query[1]] = response
                    await flood(response)
                else:
                    response = "? " + message
            elif query[0] == "WHATSAT":
                try:
                    if query[1] not in locations or int(query[2]) > 50 or int(query[3]) > 20:
                        response = "? " + message
                    else:
                        json_response = await whats_at(locations[query[1]].split()[5], query[2], int(query[3]))
                        response = locations[query[1]] + "\n" + re.sub('\n+', '\n', json_response.strip()) + "\n\n"
                except ValueError:
                    response = "? " + message
            log.write("Response: " + response + "\n")
            log.flush()
            writer.write(response.encode())
            await writer.drain()
            writer.close()
    except ConnectionError:
        log.write("Error: Connection from client dropped\n")
        log.flush()
        writer.close()


async def main():
    if len(sys.argv) != 2:
        print("Incorrect number of arguments: Please only enter the server name")
        sys.exit(1)
    elif sys.argv[1] not in ports:
        print("Invalid server name: Please choose Goloman, Hands, Holiday, Welsh, or Wilkes")
        sys.exit(1)
    else:
        global server_name
        server_name = sys.argv[1]

    global log
    log = open(server_name + "_log", "a+")

    global server
    server = await asyncio.start_server(
        handle_echo, '127.0.0.1', ports[server_name])

    addr = server.sockets[0].getsockname()

    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.close()
        exit(0)

