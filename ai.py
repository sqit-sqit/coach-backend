from openai import OpenAI
client = OpenAI()

@app.post("/ai/coach")
async def coach_chat(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Jesteś AI Coachem."},
                  {"role": "user", "content": prompt}]
    )
    return {"reply": response.choices[0].message.content}   