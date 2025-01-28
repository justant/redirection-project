class TW:
    def __init__(self, user_name, user_id, date, text, photos=None, videos=None, is_quote=False, quoted_tweet=None):
        """
        :param user_name: 트위터 사용자 이름 (예: Elon Musk)
        :param user_id: 트위터 사용자 ID (예: @elonmusk)
        :param date: 트윗 작성 날짜
        :param text: 트윗 본문
        :param photos: 사진 리스트 (URL 리스트)
        :param videos: 동영상 리스트 (URL 리스트)
        :param is_quote: 재인용 여부 (True/False)
        :param quoted_tweet: 인용 트윗 객체 (TW 객체)
        """
        self.user_name = user_name
        self.user_id = user_id
        self.date = date
        self.text = text
        self.photos = photos or []
        self.videos = videos or []
        self.is_quote = is_quote
        self.quoted_tweet = quoted_tweet

    def __eq__(self, other):
        if isinstance(other, TW):
            return self.text == other.text and self.date == other.date
        return False

    def __hash__(self):
        return hash((self.text, self.date))

    def __str__(self):
        info = f"사용자: {self.user_name} (@{self.user_id})\n"
        info += f"날짜: {self.date}\n"
        info += f"본문: {self.text}\n"
        if self.photos:
            info += f"사진: {', '.join(self.photos)}\n"
        if self.videos:
            info += f"동영상: {', '.join(self.videos)}\n"
        if self.is_quote and self.quoted_tweet:
            info += f"재인용 트윗:\n{str(self.quoted_tweet)}\n"
        return info