# Diligence — Beta Tester Guide

Thanks for helping us test Diligence! This guide walks you through setup, what to test, and how to give us useful feedback. No technical experience needed.

---

## What is Diligence?

Diligence is a fitness app that runs on your own computer. You earn points for workouts, food logging, and healthy habits, then spend them on rewards you choose. Everything stays on your machine — no cloud accounts, no data collection, no subscriptions.

---

## Setting Up (10 minutes)

### Step 1 — Install Python

Diligence needs Python (version 3.11 or newer) installed on your computer. If you're not sure whether you have it, open a terminal and type:

```
python --version
```

If it says `Python 3.11` or higher, you're good — skip to Step 2.

**If you need to install Python:**

- **Windows:** Go to https://www.python.org/downloads/ and click the big yellow "Download" button. During installation, **check the box that says "Add Python to PATH"** — this is important.
- **Mac:** Go to https://www.python.org/downloads/ and download the macOS installer. Run it and follow the prompts.

After installing, close and reopen your terminal, then check again with `python --version`.

> **Note for Mac users:** You may need to type `python3` instead of `python` throughout this guide.

### Step 2 — Download Diligence

Open a terminal (on Windows, search for "Command Prompt" or "PowerShell"; on Mac, search for "Terminal") and run these commands one at a time:

```
git clone https://github.com/DiligenceWorks/Diligence.git
cd Diligence
pip install .
```

> **Don't have git?** You can also download Diligence as a ZIP file from https://github.com/DiligenceWorks/Diligence — click the green "Code" button, then "Download ZIP." Unzip it, open a terminal in that folder, and run `pip install .`

### Step 3 — Run It

```
diligence
```

Your browser will open to `http://localhost:8000`. Create an account — pick any username and password you like. That's it, you're in.

> **If `diligence` doesn't work,** try `python -m diligence` instead.

### Stopping the App

Go back to your terminal and press `Ctrl+C`. Your data is saved automatically — next time you run `diligence`, everything will be right where you left it.

---

## What to Test

We need you to actually use the app as if it were your real fitness tracker. Below are the areas we'd love you to explore. You don't have to test everything — focus on whatever interests you, and spend at least a few days with it so you get a feel for the daily experience.

### 1. First-Time Setup (Onboarding)

When you first create an account, the app walks you through a health screening and motivation assessment. Pay attention to:

- Were the questions clear and easy to understand?
- Did any question feel confusing, irrelevant, or uncomfortable?
- Did the process feel too long, too short, or about right?
- At the end, did the app's summary of your fitness profile feel accurate?

### 2. Logging Workouts

Try logging different types of exercise — a walk, a gym session, a bike ride, yoga, whatever you actually do. Notice:

- Was it easy to find and log your activity?
- Did the points awarded feel fair for the effort?
- Did anything feel clunky or take too many clicks?
- Try logging something unusual — did the app handle it?

### 3. Food Logging

Log what you eat for a few days. The app searches a database of 400,000+ foods. Pay attention to:

- Could you find the foods you actually eat?
- Were the portion sizes and nutritional info reasonable?
- Was logging a meal quick enough that you'd actually do it daily?
- Try searching for a brand name, a generic food, and a homemade dish — how did each go?

### 4. Points and Rewards

The app has a points system with daily gates (minimums) and a reward shop. Test:

- Do you understand how points are earned?
- Does the daily gate make sense — is the minimum too easy, too hard?
- Try setting up a reward and redeeming it. Was the process clear?
- Does the points balance update correctly after activities and redemptions?

### 5. Meal Plans

If you use the meal planning feature, notice:

- Were the suggested meals realistic for your diet?
- Could you mark meals as followed or skipped easily?
- Did the compliance tracking (how well you stuck to the plan) feel accurate?

### 6. Programs (90-Day Training)

If you enroll in a training program:

- Were the scheduled workouts appropriate for your level?
- Was it clear what you were supposed to do each day?
- Did progress tracking work as expected?

### 7. General App Feel

Beyond specific features, we want to know:

- Is the app visually appealing and easy to navigate?
- Does it load quickly?
- Are there any pages that feel empty, broken, or confusing?
- Would you actually use this app day-to-day? Why or why not?
- Is there anything you expected to find but couldn't?

---

## How to Give Feedback

Good feedback is specific. Here's what helps us most:

### The Format

For each thing you notice, tell us:

1. **What you were doing** — "I was trying to log a 30-minute walk"
2. **What happened** — "The app showed 0 points even though I completed the log"
3. **What you expected** — "I expected to earn points for the activity"
4. **How it made you feel** — "Frustrating — felt like the effort wasn't recognized"

### Examples of Helpful Feedback

> "I searched for 'pad thai' in food logging and got zero results. I expected at least a generic entry. I ended up not logging my dinner because I couldn't find anything close."

> "The onboarding questions about motivation were great — I've never had a fitness app ask me WHY I exercise. The summary at the end nailed my personality. Made me want to keep using it."

> "I logged a workout and a meal on the same day but the points display only showed the workout points. After refreshing the page, both showed up. Minor but confusing."

> "The reward shop is a cool idea but I didn't understand what to put there. Maybe some example rewards would help new users get started?"

### What We Especially Want to Hear

- **Things that don't work** — errors, blank screens, buttons that do nothing
- **Things that are confusing** — where you had to guess or weren't sure what to do
- **Things that are missing** — features you looked for but couldn't find
- **Things you loved** — so we know what to keep and build on
- **Honest reactions** — if something feels pointless or annoying, say so

### How to Send It

Send your feedback to **hello@diligenceworks.online** with the subject line **"Diligence Beta Feedback"**. You can write it however you like — bullet points, paragraphs, voice-to-text, whatever works for you. Screenshots are very welcome if you can take them (on most computers: Windows key + Shift + S on Windows, Cmd + Shift + 4 on Mac).

---

## Connecting Claude to Diligence (Optional but Recommended)

You can connect Claude Desktop to Diligence so Claude can log your workouts, track your food, manage meal plans, and check your progress through conversation — just tell Claude what you did and it handles the rest.

### What You Need

- **Claude Desktop** (free) — download from https://claude.ai/download
- A Claude account (free tier works)
- Diligence running on your computer

### Setup Steps

1. Make sure Diligence is running (`python -m diligence` in your terminal)
2. Open your browser to `http://localhost:8000/agent`
3. You'll see a **Claude Desktop** section with a JSON config block — click **Copy**
4. Find your Claude Desktop config file:
   - **Windows:** Press `Win + R`, paste `%APPDATA%\Claude\claude_desktop_config.json`, press Enter
   - **Mac:** Open Finder, press `Cmd + Shift + G`, paste `~/Library/Application Support/Claude/claude_desktop_config.json`
5. Open that file in Notepad (Windows) or TextEdit (Mac)
6. Replace everything in the file with the JSON you copied. If the file doesn't exist, create it.
7. Save the file and **restart Claude Desktop**

### How to Use It

Once connected, you can talk to Claude naturally:

- *"I went for a 30-minute walk this morning"* — Claude logs the activity and tells you the points earned
- *"I had scrambled eggs and avocado for breakfast"* — Claude searches the food database and logs it with full nutrition info
- *"How am I doing today?"* — Claude shows your points, daily gate status, and what's left to earn
- *"What's my meal plan for today?"* — Claude pulls up your planned meals

### Important

- Diligence must be running in your terminal for Claude to connect. If you close the terminal, Claude loses the connection until you start Diligence again.
- You don't need Claude Desktop to use the app — the web interface works on its own. Claude is an optional power-up.

---

## Common Questions

**Where is my data stored?**
In a folder called `.diligence` in your home directory. On Windows that's `C:\Users\YourName\.diligence\`, on Mac it's `/Users/YourName/.diligence/`. It's a single file called `data.db`.

**Can I use it on my phone?**
Not as a native app, but if you run it on your computer you can open `http://your-computer-ip:8000` from your phone's browser while on the same Wi-Fi network. Run `diligence --host 0.0.0.0` to allow connections from other devices.

**Will I lose my data if I close the terminal?**
No. Your data is saved to disk continuously. Closing the terminal stops the app, but next time you run `diligence` everything is still there.

**Something broke and I want to start fresh.**
Delete the `.diligence` folder in your home directory and run `diligence` again. You'll go through onboarding as a new user.

**I got an error when installing.**
Make sure your Python version is 3.11 or newer (`python --version`). If you see "pip not found," try `python -m pip install .` instead of `pip install .`

---

## Uninstalling

If you want to remove Diligence completely:

```
pip uninstall diligence
```

Then delete the `.diligence` folder from your home directory if you want to remove your data too.

To remove the downloaded source code, just delete the `Diligence` folder wherever you cloned or unzipped it.

---

Thank you for testing. Every piece of feedback makes the app better for everyone.

*— The Diligence Team at DiligenceWorks Pte. Ltd.*
