import re

class KoreanCleaner:
    @staticmethod
    def clean(text: str) -> str:
        """
        Cleans Korean text by removing unnecessary spaces.
        
        Rules:
        1. Remove space before post-positions (조사): 은, 는, 이, 가, 을, 를, 의, 에, 로, 와, 과, 만, 도, 서, 께서, 부터, 까지
        2. Remove space before certain endings (어미): 다, 요, 죠, 네
        3. Replace multiple spaces with a single space.
        """
        # 1. Josa (Post-positions) & Endings (어미) attachment
        # Safe linguistic joining (e.g., "고양이 를" -> "고양이를")
        post_positions = "은|는|이|가|을|를|의|에|로|로서|로써|와|과|만|도|서|께서|부터|까지|하고|이랑|나|이나|처럼|만큼|보다|라고|고|마다|조차|든지|라도"
        endings = "다|요|죠|네|마|나|니|까|던|게|걸|지|려|해|세|데|구나|군요|네요|어야|아요|어요|지요|듯이|면서|니까|니까요|었|았|였|엇|앗|았어|었어|어서|아서|는건|는게|은걸|는걸|라니|니깐|텐데|에요|예요|된|함|킴|됨|임|함다|군|아진|어해|이라|이라서|이라며"
        combined = post_positions + "|" + endings
        
        # Apply iteratively to handle chains like "후원 이 라니" or "이라 고 요"
        for _ in range(4):
            text = re.sub(r'(\S)\s+(' + combined + r')(?=[\s.,!?]|$)', r'\1\2', text)
        
        # 2. Pattern Dictionary (Specific high-frequency broadcast errors & LLM artifacts)
        KNOWN_BROKEN_PATTERNS = {
            "보 니": "보니", "개 발자": "개발자", "들어 왔": "들어왔", "알 고": "알고", "생 각": "생각",
            "기 억": "기억", "후원이 라니": "후원이라니", "그렇 구나": "그렇구나", "반가 워요": "반가워요",
            "발 견": "발견", "있 늘": "있는", "짜 는": "짜는", "하 네요": "하네요", "하 죠": "하죠",
            "발견 된": "발견된", "한 거": "한거", "할 거": "할거", "거 에요": "거에요", "건 데요": "건데요",
            "무미건 조한": "무미건조한", "도망가려 고": "도망가려고", "오히 려": "오히려", "샘플 이라니": "샘플이라니",
            "이라 니까": "이라니까", "이라 고": "이라고", "이라 고요": "이라고요"
        }
        for broken, fixed in KNOWN_BROKEN_PATTERNS.items():
            text = text.replace(broken, fixed)

        # 3. Cleanup space before punctuation
        text = re.sub(r'(\S)\s+([.,!?])', r'\1\2', text)

        # 4. Multiple spaces collapse
        text = re.sub(r'\s{2,}', ' ', text)

        # 4. Cleanup space before punctuation
        text = re.sub(r'(\S)\s+([.,!?])', r'\1\2', text)

        # 5. Multiple spaces
        text = re.sub(r'\s{2,}', ' ', text)
        
        return text.strip()
