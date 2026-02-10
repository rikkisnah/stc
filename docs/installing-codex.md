### Installing Codex CLI with Oracle Code Assist

**Target audience**: Oracle internal developers with access to Oracle Code Assist (OCA).  
**Prerequisites**:
- macOS (recommended) or Linux; 
- Homebrew installed (for easiest paths)
- Oracle Code Assist permissions:  
  - Oracle Code Assist API Key Access  
  - Oracle Code Assist OpenAI GPT 5.1 Codex Access  
  - Oracle Code Assist OpenAI GPT 5.2 Access  
  (If you see 404 errors later, check permissions here: https://confluence.oraclecorp.com/confluence/display/AAGE/FAQs → "What permissions I need for OCA AI LLM")

**Reference**: https://confluence.oraclecorp.com/confluence/display/OCICODE/Installing+Codex+CLI+and+Codex+IDE+with+Oracle+Code+Assist

#### Step 1: Install Codex CLI

**Option 1 – npm (recommended for developers – gives you the latest features & easy upgrades)**

1. Install Node.js (skip if you already have npm ≥ 10 and Node ≥ 20/22 LTS):
   ```bash
   brew install node
   ```
   OR download the macOS pkg installer: https://nodejs.org/en/download

2. Install Codex CLI globally:
   ```bash
   npm install -g @openai/codex
   ```

3. (Recommended) Force-upgrade to the absolute latest version:
   ```bash
   npm install -g @openai/codex@latest --force
   ```

**Option 2 – Homebrew (simpler if you prefer zero Node dependency)**

```bash
brew install codex
```

Upgrade anytime later:
```bash
brew upgrade codex
```

Verify installation (both methods):
```bash
codex --version
```
You should see something like `codex-cli 0.x.y`.

#### Step 2: Set Up Configuration (~/.codex/config.toml)

Oracle Code Assist usually provides a pre-configured `config.toml` tailored for internal models/providers (e.g. pointing to Oracle-hosted OpenAI-compatible endpoints instead of public api.openai.com).

1. Locate or copy the provided `config.toml` file (often shared via Confluence, email, or team drive).
2. Place it in the correct location:
   ```bash
   mkdir -p ~/.codex
   cp /path/to/your-provided/config.toml ~/.codex/config.toml
   ```

   This file typically configures:
   - Model provider (Oracle-specific endpoint)
   - Default models (e.g. GPT-5.1 Codex, GPT-5.2)
   - Any internal auth/proxy settings

#### Step 3: Authenticate with Oracle Code Assist API Key

1. Go to the internal API key portal:  
   https://apex.oraclecorp.com/pls/apex/r/oca/api-key/home

2. Click **"Copy Codex Environment Setup Command"** (or similar button – it generates a ready-to-paste command).

3. Paste and run it in your terminal (iTerm recommended).  
   Example of what it looks like:
   ```bash
   echo 'eyJRik...very-long-base64-token...' | codex login --with-api-key
   ```

   This command:
   - Stores the token securely in `~/.codex/` (usually as a credential file or keychain entry)
   - Configures Codex CLI to use Oracle's authenticated endpoint

   **Note**: Do **not** use a standard `export OPENAI_API_KEY=sk-...` — Oracle Code Assist uses a different auth flow.

#### Step 4: Test Codex CLI

1. Open a terminal and navigate to any project directory (or an empty folder for testing):
   ```bash
   cd ~/projects/my-test-repo
   ```

2. Launch Codex:
   ```bash
   codex
   ```

3. At the prompt, type something simple:
   ```
   hello world
   ```
   → You should get a friendly response from the model (confirms auth, config, and model access are working).

   Try a real coding task next, e.g.:
   ```
   Write a Python function that calculates Fibonacci numbers with memoization
   ```

#### Common Errors & Fixes

- **404 Not Found** or auth failures → Missing permissions. Review:  
  https://confluence.oraclecorp.com/confluence/display/AAGE/FAQs  
  (Key groups: Oracle Code Assist API Key Access + Codex model accesses)

- **Command not found** → Installation path issue. Ensure `npm globals` or Homebrew bin is in your `$PATH`, or run:
  ```bash
  hash -r    # refresh shell cache
  ```

- **Model not available** → Wrong/default config.toml or insufficient model entitlement (GPT-5.1/5.2 Codex). Re-check Step 2 and permissions.

- **Token expired/invalid** → Regenerate via the APEX portal and re-run the login command.

Once everything works, you're ready to use Codex CLI for real development tasks inside Oracle Code Assist. Enjoy the productivity boost!
