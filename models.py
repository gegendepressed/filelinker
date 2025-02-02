from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, BigInteger, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from flask_login import UserMixin
from typing import List,Optional
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base, UserMixin):
    __tablename__ = "user"

    username: Mapped[str] = mapped_column(String(30), primary_key=True)
    fullname: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(300), nullable=False)
    file_urls: Mapped[List["FileURL"]] = relationship("FileURL", back_populates="user", cascade="all, delete-orphan")
    message: Mapped[list["Message"]] = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    def __str__(self) -> str:
        return (
            f"\nUsername: {self.username}"
            f"\nEmail: {self.email}"
            f"\nPassword: {self.password}"
            f"\nName: {self.fullname}"
            f"\nFile URLs: {self.file_urls}"
        )

    def get_id(self):
        return self.username

class FileURL(Base):
    __tablename__ = "fileurl"

    id: Mapped[int] = mapped_column(primary_key=True) 
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    shortened_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.username"))
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="file_urls")


    def __str__(self) -> str:
        return (
            f"\nFile ID: {self.id}"
            f"\nURL: {self.url}"
            f"\nShortened URL: {self.shortened_url}"
            f"\nUser ID: {self.user_id}"
            f"\nTimestamp: {self.timestamp}"
        )

class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)  # Added title field
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.username"))
    image: Mapped[Optional[str]] = mapped_column(String(400))
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    shareable_msg: Mapped[bool] = mapped_column(Boolean, default=False)
    user: Mapped["User"] = relationship("User", back_populates="message")

    def __str__(self) -> str:
        return (
            f"\nMessage ID: {self.id}"
            f"\nTitle: {self.title}"
            f"\nMessage: {self.message}"
            f"\nUser ID: {self.user_id}"
            f"\nTimestamp: {self.timestamp}"
            f"\nImage_URl: {self.image}"
        )

db = SQLAlchemy(model_class=Base)