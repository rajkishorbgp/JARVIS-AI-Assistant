import os
import openai
from config import apikey

openai.api_key = apikey

response = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {
      "role": "system",
      "content": "how to write mail to boss for reigning later "
    },
    {
      "role": "user",
      "content": ""
    }
  ],
  temperature=1,
  max_tokens=256,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0
)

print(response)


'''
{
  "id": "chatcmpl-7gs6lGxUACb5juT0ahSpDqyvz5a44",
  "object": "chat.completion",
  "created": 1690452123,
  "model": "gpt-3.5-turbo-0613",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Dear [Boss's Name],\n\nI hope this email finds you well. I wanted to bring something to your attention regarding my work schedule for the upcoming week.\n\nDue to some unforeseen personal circumstances, I would like to request permission to start later than usual on [specific date(s)]. I understand that this may disrupt the normal office routine slightly, but I assure you that I will make every effort to ensure that my work is not affected and that all my responsibilities are met.\n\nI fully understand the importance of punctuality and meeting job requirements, which is why I am reaching out to you with this request. I believe that this temporary adjustment to my schedule will allow me to address and resolve the personal matter efficiently, without compromising my work.\n\nI am more than willing to extend my work hours or come in earlier on other days to make up for the time missed during my later arrival. Additionally, I would appreciate any guidance or recommendations you may have on how to best manage this situation.\n\nThank you for your understanding and support in this matter. I am confident that with your assistance, I will be able to handle this situation while maintaining high productivity levels. Please let me know if there is anything else I can do to ensure a smooth transition during this time.\n\nBest regards,\n\n[Your Name]"
      },
      "finish_reason": "length"
    }
  ],
  "usage": {
    "prompt_tokens": 21,
    "completion_tokens": 256,
    "total_tokens": 277
  }
}
'''