import asyncio

ports = {
        "Goloman": 12759,
        "Hands": 12760,
        "Holiday": 12761,
        "Wilkes": 12762,
        "Welsh": 12763
}


async def tcp_client(message, server):
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', ports[server])

    print(f'Send: {message}')
    writer.write(message.encode())
    writer.write_eof()
    await writer.drain()
    data = await reader.read()
    print(f'Received: {data.decode()}')

    writer.close()
    print('Closed the connection')

asyncio.run(tcp_client('IAMAT kiwi.cs.ucla.edu +34.068930-118.45127 1520023934.918963997', 'Goloman'))
asyncio.run(tcp_client('WHATSAT kiwi.cs.ucla.edu 10 5', 'Wilkes'))
