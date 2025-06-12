# Afternoon Session 4: Refactor Employee Interview to Use Predefined Questions

## Goal
Modify the employee interview process (`employee_app.py` and related backend endpoints) to follow a sequence of predefined questions instead of generating each bot response dynamically using the LLM. The LLM (Groq) will still be used for backend analysis tasks like report generation and sentiment analysis on the collected responses.

## Assumptions

*   A fixed set of interview questions is sufficient for the standard employee exit interview.
*   The LLM (Groq) is still required and configured for backend tasks (reporting, sentiment analysis) operating on the stored interview data.
*   The core flow of login -> interview -> completion remains the same for the user.

## Proposed Changes Overview

1.  **Define Question Set:** Create a canonical, ordered list of questions.
2.  **Backend API (`/api/interviews/`) Modifications:**
    *   `POST /` (`create_interview`): Instead of calling LLM, retrieve and return the *first* predefined question.
    *   `POST /{id}/messages` (`send_message`): Store the user's response. Instead of calling LLM, determine and return the *next* predefined question based on the interview progress. Signal completion after the last question.
3.  **Frontend (`employee_app.py`) Modifications:**
    *   The frontend already expects a `current_question` structure. Ensure it correctly handles the questions received from the updated backend endpoints.
    *   Minor adjustments might be needed depending on the exact data structure returned by the modified backend.

## Detailed Plan & Steps

1.  **Define Predefined Questions:** [COMPLETED]
    *   **Action:** Create a Python list or dictionary defining the ordered sequence of questions.
    *   **Location:** Store this list in a suitable place, e.g., a new file `exitbot/app/core/interview_questions.py` or directly within `exitbot/app/api/endpoints/interviews.py` if simple enough.
    *   **Result:** Created `exitbot/app/core/interview_questions.py` with `PREDEFINED_QUESTIONS` list and `get_question_by_order` helper.
    *   **Example:**
      ```python
      # exitbot/app/core/interview_questions.py
      PREDEFINED_QUESTIONS = [
          {"id": 1, "text": "What was your primary reason for leaving the company?"},
          # ... 19 more questions ...
      ]
      ```

2.  **Backend - Track Interview Progress:**
    *   **Goal:** Need a way to know which question to ask next.
    *   **Option A (Simpler): Count Responses:** In `send_message`, count existing `Response` records for the interview using `crud.get_responses_by_interview`. The count indicates how many answers have been given, allowing us to determine the index of the next question.
    *   **Option B (More Explicit): Add DB Field:** Add an integer field like `current_question_index` to the `Interview` model (`exitbot/app/db/models.py`). Update this index in `send_message`. Requires DB migration/recreation.
    *   **Decision:** Implemented using **Option A (Count Responses)** within `send_message`.

3.  **Backend - Update `create_interview` (`POST /api/interviews/`):** [COMPLETED]
    *   **File:** `exitbot/app/api/endpoints/interviews.py`
    *   **Action:**
        *   Removed the `try...except` block that calls `llm_client.chat()`.
        *   Imported `get_question_by_order` from `exitbot.app.core.interview_questions`.
        *   Retrieved the first question using `get_question_by_order(1)`.
        *   Stored this first question using `crud.create_response` (with `employee_message=None`, `bot_response=first_question['text']`, `question_id=first_question['id']`).
        *   Constructed the `initial_message` object (`MessageSchema`) using the first question's details and included it in the `InterviewWithInitialMessage` response.

4.  **Backend - Update `send_message` (`POST /api/interviews/{id}/messages`):** [COMPLETED]
    *   **File:** `exitbot/app/api/endpoints/interviews.py`
    *   **Action:**
        *   Removed the logic that calls `llm_client.chat()`.
        *   Fetched previous responses using `crud.get_responses_by_interview`.
        *   Determined the next question order based on `len(previous_responses) + 1`.
        *   Imported `get_question_by_order`.
        *   If a next question exists (using `get_question_by_order`):
            *   Got the next question dict.
            *   Stored the user's current message (`message_in.content`) and the *next* bot question (`next_question['text']`) together in a new `Response` record using `crud.create_response`, including the `next_question['id']`.
            *   Returned a `MessageSchema` containing the next question text.
        *   If no next question exists (end of interview):
            *   Stored the user's final message (`message_in.content`) along with a concluding bot message in a final `Response` record.
            *   Updated the `Interview` status to `COMPLETED` and set `completed_at` using `crud.update_interview`.
            *   Returned a `MessageSchema` containing the concluding message.

5.  **Backend - Update Response Schema (if necessary):**
    *   **File:** `exitbot/app/schemas/interview.py`
    *   **Check:** The `send_message` endpoint currently returns a `MessageSchema`. This *seems* okay for now, as the frontend primarily cares about the `content` of the message (which is the next question or the concluding remark). We might revisit this if the frontend requires more explicit state information (like `is_complete`).
    *   **Action:** **HOLD** - No changes needed immediately. Let's see if frontend adjustments require this.

6.  **Frontend - API Client (`api_client.py`):**
    *   **Check:** The `send_interview_message` function expects a dictionary-like response and accesses `['content']`. Since the modified backend still returns a `MessageSchema` (which gets serialized to a dict with a `content` key), this *should* still work without changes.
    *   **Action:** **HOLD** - No changes likely needed. Verify during testing.

7.  **Frontend - Employee App (`employee_app.py`):**
    *   **Check:** Review the logic in `_display_interview_interface`. It receives the message content and displays it. It determines completion based on a specific "Thank you..." message.
    *   **Action:** The modified `send_message` now sends a specific concluding message ("Thank you for completing the exit interview..."). We need to ensure the frontend correctly identifies this message to set `st.session_state.interview_complete = True`. Let's check the exact logic in `employee_app.py`.

## Potential Challenges

*   **State Management:** Ensuring the question sequence logic based on response count is robust.
*   **Schema Consistency:** Making sure the structure of the question data returned by the backend matches what the frontend expects.
*   **Database Recreation:** If Option B (DB field) for progress tracking is chosen later, requires careful migration/recreation.

## Next Steps

1.  Confirm this plan. [DONE]
2.  ~~Start implementation, likely beginning with Step 1 (Defining Questions) and Step 3 (Modifying `create_interview`).~~ [DONE]
3.  **Review Frontend:** Check `employee_app.py` (Step 7) to ensure the completion logic matches the new concluding message from the backend.
4.  **Testing:** Thoroughly test the entire employee interview flow.
5.  **Refinement:** Address any issues found during testing, potentially revisiting Step 5 or 6 if schema/API client changes are needed. 