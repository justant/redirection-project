import requests

def handle_new_tweets(tweets):
    """
    새로운 트윗을 처리합니다.
    - 출력하거나,
    - 3rd party 서버로 전달.
    """
    for tweet in tweets:
        print(f"새로운 트윗: {tweet}")
        #send_to_server(tweet)

def send_to_server(tweet):
    """
    새로운 트윗을 3rd party 서버에 전달합니다.
    """

    # GPT를 통해서 번역 및 정리
    # 여러가지 버전 (경상도 민철쓰, 머스크 스타일, 김문스 스타일, 코인전문가)
    # 쇼츠 제작
    # telegram으로 전송
    # kakao talk으로 전송
    # twiter에 upload
    #
    try:
        url = "https://your-3rd-party-server.com/api/new-tweet"
        payload = {"tweet": tweet}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            print(f"트윗이 서버로 성공적으로 전송되었습니다: {tweet}")
        else:
            print(f"서버로 전송 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"서버 통신 중 에러 발생: {e}")
