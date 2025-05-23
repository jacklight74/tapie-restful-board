from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from tortoise import fields, models
from tortoise.contrib.fastapi import register_tortoise
from datetime import datetime
import uvicorn

app = FastAPI(
    title="익명 게시판 API",
    description="로그인 없이 사용할 수 있는 간단한 익명 게시판 RESTful API입니다.",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tortoise ORM 모델 정의
class Post(models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=200)
    content = fields.TextField()
    username = fields.CharField(max_length=100, null=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "posts"
        ordering = ["-created_at"]  # 기본 정렬: 최신순


# Pydantic 스키마 정의
class PostCreate(BaseModel):
    title: str
    content: str
    username: str


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


# 게시글 작성 API
@app.post("/posts", response_model=PostOut, summary="게시글 작성", tags=["Posts"])
async def create_post(post: PostCreate):
    """
    게시글을 작성합니다.
    - **title**: 게시글 제목
    - **content**: 게시글 내용
    - **username**: 작성자 이름
    """
    obj = await Post.create(
        title=post.title, content=post.content, username=post.username
    )

    return PostOut(
        id=obj.id,
        title=obj.title,
        content=obj.content,
        username=obj.username,
        created_at=obj.created_at,
    )


# 최근 30개 게시글 조회 API
@app.get(
    "/posts",
    response_model=List[PostOut],
    summary="최근 게시물 조회 (최대 30개 제한)",
    tags=["Posts"],
)
async def get_recent_posts():
    """
    최근 작성된 게시글을 최신순으로 반환합니다.
    """
    posts = await Post.all().order_by("-created_at").limit(30)
    return [
        PostOut(
            id=p.id,
            title=p.title,
            content=p.content,
            username=p.username,
            created_at=p.created_at,
        )
        for p in posts
    ]


# Tortoise ORM과 FastAPI 연동 설정
register_tortoise(
    app,
    db_url="sqlite://board.db",
    modules={"models": ["main"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# 서버 실행 코드 (uvicorn)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
