# ExitBot User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [HR Administrator Guide](#hr-administrator-guide)
   - [Dashboard Overview](#dashboard-overview)
   - [Managing Exit Interviews](#managing-exit-interviews)
   - [Viewing Reports](#viewing-reports)
   - [User Management](#user-management)
   - [System Settings](#system-settings)
3. [Employee Guide](#employee-guide)
   - [Starting Your Exit Interview](#starting-your-exit-interview)
   - [Interacting with ExitBot](#interacting-with-exitbot)
   - [Completing the Interview](#completing-the-interview)
4. [Interpreting Reports](#interpreting-reports)
   - [Exit Interviews Summary](#exit-interviews-summary)
   - [Sentiment Analysis](#sentiment-analysis)
   - [Trend Analysis](#trend-analysis)
5. [System Limitations](#system-limitations)
6. [Troubleshooting](#troubleshooting)

## Introduction

ExitBot is an AI-powered exit interview platform designed to streamline the employee exit process. The system uses natural language processing to conduct conversational exit interviews, analyze responses, and generate insights about employee departures.

This guide covers the functionality available to HR administrators and departing employees, as well as best practices for using the system.

## HR Administrator Guide

### Dashboard Overview

When you log in as an HR administrator, you'll see the main dashboard with the following sections:

1. **Summary Statistics**: Shows key metrics including:
   - Total exit interviews conducted
   - Completion rate
   - Average sentiment score
   - Top reasons for departures

2. **Recent Interviews**: Lists the most recent exit interviews, their status, and completion dates

3. **Department Breakdown**: Visual representation of exit interviews by department

4. **Navigation Menu**: Access to all system features

![Dashboard Screenshot](dashboard.png)

### Managing Exit Interviews

#### Creating a New Exit Interview

1. Click the **New Interview** button in the top right corner
2. Enter the employee's information:
   - Name
   - Email
   - Department
   - Last working day
3. Click **Create Interview**
4. The system will send an email invitation to the employee with a unique access link

#### Viewing Interview Details

1. From the dashboard, click on any interview in the **Recent Interviews** list
2. Alternatively, go to **Interviews** in the navigation menu and search for the desired interview
3. The interview details page shows:
   - Employee information
   - Interview status
   - All questions and responses
   - Sentiment analysis
   - Generated summary and insights

#### Managing Interview Status

Interviews can have the following statuses:

- **Pending**: Interview invitation sent but not started
- **In Progress**: Employee has started but not completed the interview
- **Completed**: Employee has finished the interview
- **Canceled**: Interview has been canceled

To change an interview status:

1. Go to the interview details page
2. Click the **Actions** button
3. Select **Change Status**
4. Choose the desired status and confirm

### Viewing Reports

#### Generating Reports

1. Go to the **Reports** section in the navigation menu
2. Select the report type:
   - Exit Interview Summary
   - Sentiment Analysis
   - Department Breakdown
   - Trend Analysis
3. Configure the report parameters:
   - Date range
   - Departments to include
   - Grouping options
4. Click **Generate Report**

#### Exporting Reports

Reports can be exported in several formats:

1. From any report view, click the **Export** button
2. Select the format:
   - PDF
   - Excel
   - CSV
   - JSON
3. Choose what to include:
   - Summary statistics
   - Detailed data
   - Charts and visualizations
4. Click **Export** to download the file

### User Management

#### Adding New Users

1. Go to **Settings > User Management**
2. Click **Add User**
3. Enter user details:
   - Name
   - Email
   - Role (HR Admin or Standard User)
   - Department
4. Click **Create User**
5. The system will send an invitation email to set up a password

#### Managing Existing Users

1. Go to **Settings > User Management**
2. Search for a user by name or email
3. Click on a user to view their details
4. From the user detail page, you can:
   - Edit user information
   - Change user role
   - Disable/enable account
   - Reset password

### System Settings

#### Configuring Interview Questions

1. Go to **Settings > Interview Templates**
2. Select the template to modify
3. You can:
   - Reorder questions using drag and drop
   - Edit existing questions
   - Add new questions
   - Disable questions
4. Click **Save Changes** when done

#### Configuring LLM Settings

1. Go to **Settings > AI Configuration**
2. You can adjust:
   - Conversation style (formal, casual)
   - Follow-up question frequency
   - Sentiment analysis sensitivity
   - Report detail level
3. Click **Save Changes** when done

## Employee Guide

### Starting Your Exit Interview

1. Check your email for an invitation from ExitBot
2. Click the unique link in the email
3. You'll be taken directly to the interview interface
4. No login is required - the link provides secure, one-time access

### Interacting with ExitBot

1. ExitBot will greet you and explain the purpose of the exit interview
2. Answer questions naturally, as if talking to a person
3. You can:
   - Provide as much or as little detail as you're comfortable sharing
   - Skip questions by typing "skip" or "next question"
   - Ask to go back to previous questions
   - Take breaks and return later using the same link

#### Sample Conversation

```
ExitBot: Hello Jane, I'm ExitBot. I'll be conducting your exit interview today. 
         This conversation will help us understand your experience at the company 
         and identify areas for improvement. What is your primary reason for leaving?

You: I received a job offer with better growth opportunities.

ExitBot: Thank you for sharing that. Could you elaborate on what specific growth 
         opportunities were missing in your current role?

You: I felt that there wasn't a clear path for advancement in my department, 
     and I wasn't getting opportunities to develop new skills.

ExitBot: I understand. What aspects of your job did you enjoy the most during 
         your time with us?
```

### Completing the Interview

1. After answering all questions, ExitBot will ask if you have any additional feedback
2. You can add any final thoughts or comments
3. Once complete, ExitBot will thank you and the interview will be marked as finished
4. You'll receive a confirmation email with a summary of your responses

## Interpreting Reports

### Exit Interviews Summary

The summary report provides a high-level overview of exit interviews and includes:

1. **Completion Metrics**:
   - Number of interviews conducted vs. invited
   - Average completion time
   - Completion rate by department

2. **Key Insights**:
   - Most common reasons for departure
   - Most positively mentioned aspects of the company
   - Most frequently mentioned areas for improvement

3. **Recommendations**:
   - AI-generated recommendations based on interview responses
   - Priority levels for addressing issues
   - Comparison to industry benchmarks (if available)

### Sentiment Analysis

The sentiment analysis report shows:

1. **Overall Sentiment**:
   - Average sentiment score (-1.0 to 1.0)
   - Sentiment distribution (positive, neutral, negative)

2. **Sentiment by Category**:
   - Management
   - Compensation
   - Work-life balance
   - Career growth
   - Company culture

3. **Sentiment Trends**:
   - Change over time
   - Comparison by department

### Trend Analysis

The trend report shows how exit data changes over time:

1. **Departure Rate Trends**:
   - Monthly/quarterly departure rates
   - Seasonal patterns

2. **Reason Trends**:
   - Changes in top departure reasons over time
   - Emerging issues

3. **Sentiment Trends**:
   - Changes in sentiment scores over time
   - Department-specific trends

## System Limitations

ExitBot has some limitations to be aware of:

1. **Language Understanding**:
   - While ExitBot can understand natural language, very complex or nuanced responses might be misinterpreted
   - Technical jargon specific to your company might not be fully understood

2. **Follow-up Questions**:
   - ExitBot may occasionally ask follow-up questions that seem redundant if it doesn't recognize that a topic was already covered

3. **Sentiment Analysis**:
   - Sarcasm and certain cultural expressions may be misinterpreted in sentiment analysis
   - The sentiment scale is relative and should be used for comparison rather than absolute judgment

4. **AI Limitations**:
   - ExitBot cannot provide real-time human intervention if an employee becomes distressed
   - As an AI system, it cannot fully replace the empathy and adaptability of a human interviewer

## Troubleshooting

### Common Issues

#### Interview Link Not Working

If an employee reports that their interview link isn't working:

1. Verify that the interview is still active in the system
2. Check that the employee is using the exact link from the email
3. Ensure the interview hasn't already been completed
4. If needed, generate a new link by going to the interview details page and clicking **Resend Invitation**

#### Interview Shows Incomplete but Employee Completed It

If an interview is showing as incomplete but the employee says they completed it:

1. Check the last response timestamp
2. Verify if the final confirmation message was sent
3. If it appears the interview was almost complete, you can manually mark it as completed from the interview details page

#### Report Generation Errors

If you encounter errors when generating reports:

1. Try narrowing the date range
2. Reduce the number of departments included
3. If the issue persists, try exporting the raw data and creating a custom report

### Getting Help

For additional support:

1. Click the **Help** icon in the top right corner
2. Check the FAQ section for common questions
3. Submit a support ticket with details of your issue
4. For urgent issues, contact your system administrator 