import sqlalchemy
from fastapi import APIRouter, HTTPException
from src import database as db
from pydantic import BaseModel
from typing import List
from src.datatypes import Conversation, Line
from datetime import datetime


# FastAPI is inferring what the request body should look like
# based on the following two classes.
class LinesJson(BaseModel):
    character_id: int
    line_text: str


class ConversationJson(BaseModel):
    character_1_id: int
    character_2_id: int
    lines: List[LinesJson]


router = APIRouter()


@router.post("/movies/{movie_id}/conversations/", tags=["movies"])
def add_conversation(movie_id: int, conversation: ConversationJson):
    """
    This endpoint adds a conversation to a movie. The conversation is represented
    by the two characters involved in the conversation and a series of lines between
    those characters in the movie.

    The endpoint ensures that all characters are part of the referenced movie,
    that the characters are not the same, and that the lines of a conversation
    match the characters involved in the conversation.

    Line sort is set based on the order in which the lines are provided in the
    request body.

    The endpoint returns the id of the resulting conversation that was created.
    """
    with db.engine.begin() as conn:
        # figure out biggest ids
        stmt = sqlalchemy.select(sqlalchemy.func.max(db.conversations.c.conversation_id))
        maxConvoID = conn.execute(stmt).scalar()
        stmt = sqlalchemy.select(sqlalchemy.func.max(db.lines.c.line_id))
        maxLineID = conn.execute(stmt).scalar()
        # Insert conversation into conversations table
        maxConvoID += 1
        conversation_values = {"conversation_id": maxConvoID,
                               "movie_id": movie_id,
                               "character1_id": conversation.character_1_id,
                               "character2_id": conversation.character_2_id}
        conversation_stmt = db.conversations.insert().values(conversation_values)
        conversation_result = conn.execute(conversation_stmt)

        # Insert lines into lines table
        for line in conversation.lines:
            line_values = {"line_id": maxLineID + 1,
                           "conversation_id": maxConvoID,
                           "character_id": line.character_id,
                           "line_text": line.line_text}
            line_stmt = db.lines.insert().values(line_values)
            conn.execute(line_stmt)
            maxLineID += 1
    return maxConvoID
