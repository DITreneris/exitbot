---
title: HR Training Guide - Predefined Questions System
category: User Guide
audience: HR Staff
created: 2025-05-02
last_updated: 2025-05-02
version: 1.0
---

# HR Training Guide: Predefined Questions System

## Overview

The Exit Interview Bot now uses a structured sequence of predefined questions instead of an AI-generated conversation. This change brings several benefits:

- More consistent interview experiences for all employees
- Faster response times (60-80% improvement)
- Improved reliability with no external API dependencies
- Better data comparability across interviews
- Reduced operational costs

## Key Differences

| Aspect | Previous LLM System | New Predefined Questions |
|--------|---------------------|--------------------------|
| Question Flow | Dynamic, based on responses | Fixed sequence of questions |
| Response Time | 2-5 seconds per message | Under 1 second per message |
| Customization | Questions varied by context | Same questions for all employees |
| Data Analysis | Required post-processing | Directly comparable responses |
| Reliability | Dependent on external API | Fully self-contained |
| Cost | Higher API usage costs | Minimal external API usage |

## Using the New System

### Interview Creation

The process for creating new interviews remains the same:

1. Log in to the HR dashboard
2. Click "Create New Interview"
3. Enter the employee's information
4. Select "Exit Interview" as the type
5. Click "Create"

The system will automatically use the predefined questions format.

### Viewing Active Interviews

Active interviews now display additional information:

- Progress indicator showing completion percentage
- Current question number and total questions
- Estimated time to completion

![Progress Indicator](https://placehold.co/600x200/1E40AF/FFFFFF?text=Progress+Indicator+Example)

### Interview Reports

Reports have been enhanced to better support the structured format:

1. **Question-Based Analysis**: Responses are now grouped by question, making it easier to compare answers across employees
2. **Completion Metrics**: Reports show completion rates and time spent on each question
3. **Response Quality**: The system now measures response length and completeness for each question
4. **Trend Analysis**: Compare responses to the same question across departments or time periods

### Data Export

When exporting data, you'll notice new fields:

- `question_id`: Unique identifier for each question
- `question_text`: The exact text of the question
- `question_category`: Category classification of the question
- `question_order`: Position in the interview sequence

## Question Set

The predefined questions cover key exit interview areas:

1. **Reasons for Leaving** (Questions 1-2)
   - Primary motivation for departure
   - Specific events or triggers

2. **Work Experience** (Questions 3-4)
   - Fulfilling aspects of the role
   - Challenges and frustrations

3. **Management & Leadership** (Questions 5-7)
   - Relationship with direct manager
   - Feedback and support
   - Leadership communication

4. **Engagement & Culture** (Questions 8-10)
   - Skills utilization
   - Team dynamics
   - Inclusion and belonging

5. **Growth & Development** (Questions 11-12)
   - Career advancement opportunities
   - Recognition and rewards

6. **Work Environment** (Questions 13-14)
   - Cultural alignment
   - Work-life balance

7. **Improvement Suggestions** (Questions 15-16)
   - Process improvements
   - Resource adequacy

8. **Future Outlook** (Questions 17-20)
   - Retention factors
   - Potential return
   - Recommendations
   - Advice for improvement

## Best Practices

### Preparing Employees

- Send employees a pre-interview notification explaining the structured format
- Encourage honest, detailed responses despite the fixed question sequence
- Remind them the interview can be paused and resumed if needed

### Reviewing Responses

- Focus on comparing responses to the same question across employees
- Look for patterns in specific question responses to identify systemic issues
- Pay attention to questions with consistently short or missing responses
- Use the category groupings to identify department-wide trends

### Follow-up Actions

- Create action items based on feedback categories (e.g., management, resources)
- Track improvements in responses to specific questions over time
- Share anonymized feedback from key questions with relevant department heads
- Use the structured data to create targeted retention initiatives

## Frequently Asked Questions

**Q: Can we customize the questions for different departments?**

A: Currently, all departments use the same question set. We plan to add department-specific questions in a future update.

**Q: What if an employee wants to provide feedback not covered by the questions?**

A: The final question ("What advice would you offer to help us improve the employee experience?") provides an opportunity for open-ended feedback.

**Q: How long does a typical interview take now?**

A: With 20 predefined questions, most interviews are completed in 15-20 minutes, compared to 25-30 minutes with the previous system.

**Q: Can employees skip questions?**

A: Yes, employees can provide empty responses to skip questions they prefer not to answer.

**Q: Will we still get sentiment analysis on responses?**

A: Yes, the system still analyzes sentiment for each response, but now provides more consistent comparisons across the same questions.

## Getting Help

If you encounter any issues with the new system:

- **Technical problems**: Contact the IT help desk at support@example.com
- **Question content**: Submit feedback through the HR portal
- **Training requests**: Email training@example.com for additional sessions

## Conclusion

The predefined questions system represents a significant improvement in reliability, consistency, and data quality for our exit interviews. While we lose some of the dynamic conversation aspects of the previous system, we gain much better comparative data and a more dependable experience for both employees and HR staff.

---

*Last updated: 2025-05-02* 