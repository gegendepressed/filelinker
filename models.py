from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, BigInteger, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from flask_login import UserMixin
from typing import List
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base, UserMixin):
    __tablename__ = "user"

    username: Mapped[str] = mapped_column(String(30), primary_key=True)
    fullname: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(300), nullable=False)
    file_urls: Mapped[List["FileURL"]] = relationship("FileURL", back_populates="user")

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
db = SQLAlchemy(model_class=Base)