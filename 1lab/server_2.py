import asyncio
import os
import time
import xml.etree.ElementTree as ET
start=False
delta_time=10
lst=[]
close=False
def get_xml_ans_by_name(process_name):
    tree = ET.parse("./data.xml")
    root = tree.getroot()
    s=""
    print("xml_2")
    for process in root.findall('process'):
        name = process.find('name').text
        if name == process_name:
            s+=process.find('result').text+'\n\n'
    print("xml_3")
    print(s)
    return (s+'\0')
async def controler():
    print("start")
    tree = ET.parse("./data.xml")
    root = tree.getroot()
    for index in range(len(lst)):
        if(close):
            break
        else:
            a=os.popen(f'python ./{lst[index][:-3]}/{lst[index]}')
            new_process = ET.Element("process")
            name = ET.SubElement(new_process, "name")
            name.text = lst[index]
            result = ET.SubElement(new_process, "result")
            
            result.text = a.read()
            root.append(new_process)
        tree = ET.ElementTree(root)
        tree.write("data.xml", encoding='utf-8', xml_declaration=True)
        time.sleep(delta_time)
async def handle_client(reader, writer):
    print("Клиент подключен.")
    os.system('chcp 65001 > nul 2>&1')
    try:
        while True:
            data = await get_data(reader)
            head=data[:3]
            body=data.replace(head+" ", '', 1)
            if not data:  # Если данных нет, клиент отключился
                continue
            else:
                if(head=="new"):#добавление нового файла
                    name=body.split()[0]
                    file = body.replace(name+" ", '', 1)
                    if not os.path.exists(f'./{name[:name.index(".")]}'):
                        os.makedirs(f'./{name[:name.index(".")]}')
                    with open(f'./{name[:name.index(".")]}/{name}', 'wb') as f:
                        f.write(file.encode())
                    f.close()
                    writer.write(("все оки файл сохранен"+ '\0').encode())
                    await writer.drain()
                elif(head=="lst"):
                    print("list")
                    items = os.listdir("./")
                    print(items)
                    directories = [item for item in items if os.path.isdir(os.path.join("", item))]
                    writer.write(("Список доступных файлов"+"\n"+str(items).replace(",","").replace("'main.py'","").replace("'server_2.py'","").replace("'data.xml'","")+ '\0').encode())
                    await writer.drain()
                elif(head=="res"):#xml получаем
                    try:
                        name=body.replace(" ","").replace("\n","")
                        print(name)
                        writer.write(get_xml_ans_by_name(name).encode())
                        await writer.drain()
                    except:
                        writer.write(("syntax error"+ '\0').encode())
                        await writer.drain()
                elif(head=="add"):#добавить запуск файла
                    try:
                        for i in body.split():
                            lst.append(i)
                        writer.write(("Добавлено в очередь!"+ '\0').encode())
                        await writer.drain()
                    except:
                        writer.write(("syntax error"+ '\0').encode())
                        await writer.drain()
                    print(lst)
                elif(head=="str"):#запуск офереди
                    try:
                        await controler()
                        writer.write(("Готово!!!"+ '\0').encode())
                        await writer.drain()
                    except:
                        writer.write(("syntax error"+ '\0').encode())
                        await writer.drain()
                elif("cls" in head):#закрыть офередь
                    try:
                        close=True
                        writer.write(("I willl be back!"+ '\0').encode())
                        await writer.drain()
                    except:
                        writer.write(("syntax error"+ '\0').encode())
                        await writer.drain()
                elif("tim" in head):#увеличить время между запусками
                    try:
                        delta_time=int(body)
                        print(1)
                        writer.write((f'Новое время :{body.split()[0]}'+ '\0').encode())
                        await writer.drain()
                    except:
                        writer.write(("syntax error"+ '\0').encode())
                        await writer.drain()
                else:
                    print("Error")
    except asyncio.CancelledError:
        pass
    finally:
        print("Клиент отключен.")
        writer.close()
        await writer.wait_closed()

async def get_data(reader):
    data = bytearray()
    while True:
        chunk = await reader.read(1024)
        if not chunk:
            break
        data.extend(chunk)
        if b'\0' in chunk:  # Если был получен байт завершения
            break
    return data[:-1].decode()

async def main():
    server = await asyncio.start_server(handle_client, 'localhost', 8000)
    print("Сервер запущен на порту 8000")

    async with server:
        await server.serve_forever()

# Запуск сервера
asyncio.run(main())
