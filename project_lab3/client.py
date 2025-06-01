import argparse, asyncio, json, sys, websockets, httpx, pathlib

REST = "http://127.0.0.1:8000"
WS_TPL = "ws://127.0.0.1:8000/ws/{uid}?token={tok}"


async def login(user_id: str) -> str:
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{REST}/api/auth/login", json={"user_id": user_id})
        r.raise_for_status()
        return r.json()["access_token"]


async def launch_parse(token: str, url: str, depth: int):
    hdr = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{REST}/api/parse", json={"url": url, "max_depth": depth}, headers=hdr)
        r.raise_for_status()
        return r.json()["task_id"]


async def run_one(url: str, depth: int, uid: str):
    token = await login(uid)
    task_id = await launch_parse(token, url, depth)
    print(f"Задача запущена id={task_id}")

    async with websockets.connect(WS_TPL.format(uid=uid, tok=token)) as ws:
        async for raw in ws:
            data = json.loads(raw)
            if data["task_id"] != task_id:
                continue
            print(json.dumps(data, ensure_ascii=False, indent=2))
            if data["status"] in ("COMPLETED", "FAILED"):
                break


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url")
    p.add_argument("--max-depth", type=int, default=2)
    p.add_argument("--user-id", default="cli")
    p.add_argument("--file", type=pathlib.Path,
                   help="Файл batch-команд формата url,max_depth на строку")
    args = p.parse_args()

    if args.file:
        tasks = []
        for line in args.file.read_text().splitlines():
            url, depth = line.split(",", 1)
            tasks.append(run_one(url.strip(), int(depth), args.user_id))
        asyncio.run(asyncio.gather(*tasks))
    else:
        if not args.url:
            sys.exit("url обязателен без --file")
        asyncio.run(run_one(args.url, args.max_depth, args.user_id))


if __name__ == "__main__":
    main()
