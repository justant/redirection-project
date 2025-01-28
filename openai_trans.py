import openai
import configparser

# OpenAI API 키 설정
config = configparser.ConfigParser()
config.read("config.properties")
openai.api_key = config.get("DEFAULT", "openai.api_key")

def analyze_and_translate_tweet(tweet_text, author_name=None):
    """
    트위터 글을 번역하고 견해를 덧붙이는 작업을 수행합니다.

    :param tweet_text: 트위터 글 원문
    :param author_name: 트윗 작성자 (예: 'Elon Musk', 'Donald Trump')
    :return: 번역된 트윗과 한 줄 견해
    """
    # 작성자 정보를 프롬프트에 추가
    author_info = f"이 글은 {author_name}이 작성한 것입니다." if author_name else "작성자는 알려지지 않았습니다."
    messages = [
        {"role": "system", "content": "당신은 월스트리트에서 일하는 코인 전문 투자자입니다. 코인 시장에 대해 긍정적이고 진보적인 시각을 가지고 있습니다. 주어진 트윗을 한국어로 번역하고, 작성자의 배경을 고려한 한 줄 견해를 작성하세요."},
        {"role": "user", "content": f"{author_info}\n트윗 내용: {tweet_text}"}
    ]

    try:
        # ChatCompletion API 호출
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        )
        return response['choices'][0]['message']['content']

    except Exception as e:
        print(f"오류 발생: {e}")
        return None