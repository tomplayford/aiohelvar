from aiohelvar.exceptions import ParserError
import asyncio

from aiohelvar.parser.parser import CommandParser


LINE_ENDING = b"#"

things_to_send = []


def handle_message_from_router(message):
    print("Handling message from router: ")
    print(message)


async def communicate(data_to_send):

    print("Connecting...")
    reader, writer = await asyncio.open_connection("10.254.0.1", 50000)

    asyncio.create_task(my_reader(reader, writer))
    asyncio.create_task(my_writer(reader, writer, data_to_send))

    while not writer.is_closing():
        await asyncio.sleep(2)

    # We're closing... TODO: Do something.


async def my_writer(reader, writer, data_to_send):

    while True:
        await data_to_send.wait()
        if len(things_to_send) > 0:
            thing = things_to_send.pop()
            print(f"found {thing} to send. Sending...")
            writer.write(thing)
            await writer.drain()
            print("Sent!")
        else:
            data_to_send.clear()


async def my_reader(reader, writer):
    # an echo server
    print("Connected.")
    parser = CommandParser()

    while True:
        line = await reader.readuntil(LINE_ENDING)
        if line is not None:

            print(f"We've received the following: {line}")
            try:
                command = parser.parse_command(line)
            except ParserError as e:
                print(e)
            else:
                print(f"Found the following command: {command}")
        await asyncio.sleep(1)


async def main():
    data_to_send = asyncio.Event()
    asyncio.create_task(communicate(data_to_send))

    def send_data(data):
        things_to_send.append(data)
        data_to_send.set()

    send_data(b">V:2,C:101#")

    await asyncio.sleep(5)

    print(f"things_to_send looks like: {things_to_send}")

    send_data(b">V:2,C:102#")

    while True:
        await asyncio.sleep(100)


asyncio.run(main())
