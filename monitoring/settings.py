from pydantic import BaseSettings

class Settings(BaseSettings):
    login: str = ''
    password: str = ""
    company_key: str = "bnrl_frRFjEz8Mkn"


settings = Settings()