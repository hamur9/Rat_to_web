import asyncio
import websockets
import json

# URL WebSocket-сервера
websocket_server_url = 'ws://192.168.31.189:2025'

local_client = None


async def forward_message_to_client(message):
    """Отправляет сообщение подключённому локальному клиенту."""
    global local_client
    if local_client is not None:
        try:
            await local_client.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            print("Локальный клиент отключился.")
            local_client = None


async def handle_local_client(websocket):
    """Обрабатывает подключение локального клиента."""
    global local_client
    local_client = websocket
    try:
        print("Локальный клиент подключился.")
        while True:
            message = await websocket.recv()  # Получаем сообщение от локального клиента
            await forward_message_to_remote_server(message)  # Отправляем его на удаленный сервер
    except websockets.exceptions.ConnectionClosed:
        print("Локальный клиент отключился.")
    finally:
        local_client = None


async def forward_message_to_remote_server(message):
    """Отправляет сообщение на удаленный WebSocket-сервер и логирует ответ."""
    try:
        async with websockets.connect(websocket_server_url) as websocket:
            await websocket.send(message)  # Отправляем сообщение на удаленный сервер
            response = await websocket.recv()  # Получаем ответ от удаленного сервера
            print(f"Ответ от удаленного сервера: {response}")  # Логируем ответ
    except Exception as e:
        print('Ошибка при отправке сообщения на удаленный сервер:', e)


async def listen():
    """Подключается к удаленному WebfSocket-серверу и обрабатывает события."""
    try:
        async with websockets.connect(websocket_server_url) as websocket:
            print('Подключено к WebSocket-серверу.')

            while True:
                data = await websocket.recv()
                try:
                    # Разбираем сообщение
                    message = json.loads(data)
                    # Проверяем, является ли это событие "pedal"
                    if message.get('event') == 'pedal':
                        with open("out.txt", "a") as f:
                            f.write("1")
                            f.write("\n")
                        await forward_message_to_client(message)
                        print(f"Сообщение отправлено локальному клиенту: {message}")
                    else:
                        print('Получено сообщение другого типа:', message)
                except json.JSONDecodeError as e:
                    print('Ошибка при разборе сообщения:', e)
    except Exception as e:
        print('Ошибка WebSocket:', e)


async def main():
    """Основная функция для запуска локального сервера и подключения к WebSocket."""
    # Запускаем локальный WebSocket-сервер
    local_server = await websockets.serve(handle_local_client, "localhost", 8765)
    print("Локальный сервер запущен на ws://localhost:8765")

    # Запускаем прослушивание удаленного WebSocket-сервера
    asyncio.create_task(listen())

    await local_server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
