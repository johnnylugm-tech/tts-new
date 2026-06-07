import uvicorn
from fastapi import FastAPI, Request, Response
import httpx
import asyncio

app = FastAPI()

# LM Studio 的實際地址 - 偵測環境嘗試常見端口
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

@app.post("/v1/chat/completions")
async def proxy_chat(request: Request):
    try:
        body = await request.json()
    except Exception as e:
        return Response(content=f"Error parsing JSON: {str(e)}", status_code=400)
    
    new_messages = []
    valid_roles = {"user", "assistant"}
    
    # [關鍵邏輯] 高度魯棒的 Role 轉換與合併
    for i, msg in enumerate(body.get("messages", [])):
        role = msg.get("role")
        content = msg.get("content", "")
        
        if role in valid_roles:
            new_messages.append(msg)
        elif role == "system":
            if not new_messages:
                # 第一條就是 system，允許
                new_messages.append(msg)
            else:
                # System 出現在中間，合併到前一個訊息 (通常是 user)
                prev_msg = new_messages[-1]
                if prev_msg["role"] == "user":
                    prev_msg["content"] += f"\n\n[System Context]: {content}"
                else:
                    # 如果前一個是 assistant，則作為 user 訊息插入
                    new_messages.append({"role": "user", "content": f"[System Context]: {content}"})
        else:
            # 其他未知角色，統一轉為 user
            new_messages.append({**msg, "role": "user"})

    body["messages"] = new_messages

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(LM_STUDIO_URL, json=body)
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.ConnectError:
            return Response(content="Error: Cannot connect to LM Studio at " + LM_STUDIO_URL, status_code=502)
        except Exception as e:
            return Response(content=f"Error during proxying: {str(e)}", status_code=500)

@app.get("/health")
async def health():
    return {"status": "ok", "proxying_to": LM_STUDIO_URL}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=1235)
