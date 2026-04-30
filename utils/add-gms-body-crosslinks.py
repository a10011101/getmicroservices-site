#!/usr/bin/env python3
"""
Add contextual body cross-links to all GMS blog posts.
Does NOT touch further-reading sections.
Processes both /blog/ and /a/blog/ versions.
"""
import re
import os
import subprocess

REPO = "/root/.openclaw/workspace/gms"

# All GMS slugs for reference
ALL_SLUGS = [
    "n8n-vs-zapier-2026", "ai-agents-small-business", "make-vs-zapier",
    "automate-client-onboarding", "n8n-self-hosted-guide", "solopreneur-automation-stack",
    "ai-content-workflow", "webhook-explained", "notion-automation",
    "chatgpt-api-automation", "n8n-business-processes", "saas-onboarding-automation",
    "ai-automation-agency", "n8n-ai-agent-workflows", "zapier-make-n8n-comparison",
    "automation-agency-revenue", "n8n-social-media-automation", "ai-chatbot-for-small-business",
    "ai-inbox-triage-for-busy-executives", "automate-small-business-tasks",
    "automating-invoice-chasing-recovered-8000", "google-sheets-slack-digest-ops-teams",
    "how-to-automate-your-business", "how-to-integrate-ai-into-your-business",
    "how-we-automated-a-booking-system-in-3-days", "how-we-automated-invoice-chasing",
    "how-we-built-a-lead-qualification-bot", "lead-qualification-bot-weekend-build",
    "competitor-price-monitoring-bot", "automated-employee-timesheet-processing",
    "shopify-order-3pl-fulfilment-automation", "whatsapp-restaurant-bot-reservations-menu",
    "why-your-crm-and-stripe-dont-talk", "why-zapier-gets-expensive-fast",
    "zapier-alternative-for-agencies", "3-tool-stack-client-reporting-process"
]

# Topic groupings for smarter linking
TOPIC_GROUPS = {
    "comparison": ["n8n-vs-zapier-2026", "make-vs-zapier", "zapier-make-n8n-comparison", "why-zapier-gets-expensive-fast", "zapier-alternative-for-agencies"],
    "ai": ["ai-agents-small-business", "ai-content-workflow", "ai-chatbot-for-small-business", "ai-inbox-triage-for-busy-executives", "ai-automation-agency", "n8n-ai-agent-workflows", "how-to-integrate-ai-into-your-business", "chatgpt-api-automation"],
    "automation": ["solopreneur-automation-stack", "how-to-automate-your-business", "automate-small-business-tasks", "automate-client-onboarding", "n8n-business-processes", "webhook-explained"],
    "n8n": ["n8n-self-hosted-guide", "n8n-vs-zapier-2026", "n8n-business-processes", "n8n-social-media-automation", "n8n-ai-agent-workflows", "openclaw-n8n-integration"],
    "leads": ["how-we-built-a-lead-qualification-bot", "lead-qualification-bot-weekend-build", "ai-inbox-triage-for-busy-executives"],
    "invoice": ["automating-invoice-chasing-recovered-8000", "how-we-automated-invoice-chasing"],
    "ecommerce": ["shopify-order-3pl-fulfilment-automation", "competitor-price-monitoring-bot"],
    "bots": ["whatsapp-restaurant-bot-reservations-menu", "how-we-automated-a-booking-system-in-3-days", "competitor-price-monitoring-bot"],
    "sheets": ["google-sheets-slack-digest-ops-teams", "3-tool-stack-client-reporting-process"],
    "crm": ["why-your-crm-and-stripe-dont-talk"],
    "onboarding": ["saas-onboarding-automation", "automate-client-onboarding"],
}

def get_related_slugs(slug, count=4):
    """Get related slugs for cross-linking, excluding self."""
    related = []
    # First check if slug belongs to any topic group
    for group, members in TOPIC_GROUPS.items():
        if slug in members:
            for m in members:
                if m != slug and m not in related and m in ALL_SLUGS:
                    related.append(m)
    # Fill remaining with any other slugs
    for s in ALL_SLUGS:
        if s != slug and s not in related:
            related.append(s)
    return related[:count]

def get_body_text_for_linking(body_html):
    """Extract plain text from body HTML for matching, preserving positions."""
    # Remove HTML tags to get text positions
    parts = re.split(r'(<[^>]+>)', body_html)
    text_positions = []
    for i, part in enumerate(parts):
        if not part.startswith('<'):
            text_positions.append((i, part))
    return parts, text_positions

def add_links_to_body(body_html, slug, prefix="blog"):
    """Add contextual links to body HTML. prefix: 'blog' or 'a/blog'."""
    parts, text_parts = get_body_text_for_linking(body_html)
    
    # Get related slugs
    related = get_related_slugs(slug)
    
    # For each related slug, check if it's already linked nearby
    path_prefix = f"/{prefix}/"
    
    existing_links = set(re.findall(r'href="' + path_prefix + r'([^"]+)"', body_html))
    
    links_added = 0
    for target_slug in related:
        if links_added >= 3:
            break
        if target_slug in existing_links:
            continue
        if target_slug not in ALL_SLUGS:
            continue
        
        # Find the title of the target post to know what text to link
        # Simple approach: find text matches in plain text parts
        target_terms = {
            "n8n-vs-zapier-2026": ["n8n", "Zapier", "n8n vs Zapier", "automation tool"],
            "ai-agents-small-business": ["AI agent", "agent", "AI for small"],
            "make-vs-zapier": ["Make", "Make.com", "Make vs Zapier"],
            "automate-client-onboarding": ["client onboarding", "onboard"],
            "n8n-self-hosted-guide": ["self-host", "self host", "selfhost", "n8n setup", "n8n installation"],
            "solopreneur-automation-stack": ["solopreneur", "automation stack", "stack"],
            "ai-content-workflow": ["content creation", "content workflow", "AI content"],
            "webhook-explained": ["webhook", "API", "connect", "glue"],
            "notion-automation": ["Notion", "notion"],
            "chatgpt-api-automation": ["ChatGPT", "GPT", "API", "language model", "LLM"],
            "n8n-business-processes": ["business process", "process automation"],
            "saas-onboarding-automation": ["SaaS", "trial", "onboarding", "churn"],
            "ai-automation-agency": ["automation agency", "agency", "build an AI"],
            "n8n-ai-agent-workflows": ["AI agent workflow", "agent workflow"],
            "zapier-make-n8n-comparison": ["Zapier vs", "Make vs", "n8n vs", "compare", "comparison"],
            "automation-agency-revenue": ["agency revenue", "10k", "revenue", "agency income"],
            "n8n-social-media-automation": ["social media", "social", "post"],
            "ai-chatbot-for-small-business": ["chatbot", "chat bot", "chat bot"],
            "ai-inbox-triage-for-busy-executives": ["inbox", "triage", "email", "inbox management"],
            "automate-small-business-tasks": ["small business", "business task", "SMB"],
            "automating-invoice-chasing-recovered-8000": ["invoice", "payment chasing", "invoice chasing", "recovered"],
            "google-sheets-slack-digest-ops-teams": ["Google Sheets", "Slack", "digest", "ops team"],
            "how-to-automate-your-business": ["automate your business", "business automation"],
            "how-to-integrate-ai-into-your-business": ["integrate AI", "AI into", "AI integration"],
            "how-we-automated-a-booking-system-in-3-days": ["booking system", "booking", "reservation"],
            "how-we-automated-invoice-chasing": ["invoice chasing", "chasing"],
            "how-we-built-a-lead-qualification-bot": ["lead qualification", "qualification bot", "qualify"],
            "lead-qualification-bot-weekend-build": ["weekend build", "rapid build", "weekend project"],
            "competitor-price-monitoring-bot": ["competitor", "price monitor", "price tracking", "monitoring bot"],
            "automated-employee-timesheet-processing": ["timesheet", "employee time", "time tracking"],
            "shopify-order-3pl-fulfilment-automation": ["Shopify", "3PL", "fulfilment", "fulfillment", "order automation"],
            "whatsapp-restaurant-bot-reservations-menu": ["WhatsApp", "restaurant", "reservation", "menu bot"],
            "why-your-crm-and-stripe-dont-talk": ["CRM", "Stripe", "don't talk", "integration"],
            "why-zapier-gets-expensive-fast": ["Zapier expensive", "Zapier pricing", "Zapier cost"],
            "zapier-alternative-for-agencies": ["Zapier alternative", "agency alternative"],
            "3-tool-stack-client-reporting-process": ["reporting", "client report", "reporting stack"],
        }
        
        terms = target_terms.get(target_slug, [target_slug.replace("-", " ")])
        
        # Try to find a match in text parts
        for idx, (part_idx, text) in enumerate(text_parts):
            for term in terms:
                # Case insensitive match
                pos = text.lower().find(term.lower())
                if pos >= 0:
                    # Check not already linked near this position
                    before = text[max(0, pos-30):pos]
                    if 'href="' in before:
                        continue
                    after = text[pos+len(term):pos+len(term)+30]
                    if '</a>' in after:
                        continue
                    
                    # Get the actual text at the matched position (preserving case)
                    actual_text = text[pos:pos+len(term)]
                    
                    # Wrap in anchor tag
                    link = f'<a href="{path_prefix}{target_slug}">{actual_text}</a>'
                    new_text = text[:pos] + link + text[pos+len(term):]
                    
                    # Update the parts
                    orig_idx = text_parts[idx][0]
                    body_parts = re.split(r'(<[^>]+>)', body_html)
                    body_parts[orig_idx] = new_text
                    body_html = ''.join(body_parts)
                    
                    links_added += 1
                    existing_links.add(target_slug)
                    
                    # Rebuild text_parts after modification
                    parts = re.split(r'(<[^>]+>)', body_html)
                    text_parts = [(i, p) for i, p in enumerate(parts) if not p.startswith('<')]
                    break
            if links_added >= 3:
                break
    
    return body_html, links_added

def process_post(slug):
    """Process a single post (both /blog/ and /a/blog/ versions)."""
    total_links = 0
    
    for prefix in ['blog', 'a/blog']:
        # Check if flat .html or subdir/index.html
        file_path = os.path.join(REPO, prefix, f"{slug}.html")
        if not os.path.exists(file_path):
            file_path = os.path.join(REPO, prefix, slug, "index.html")
        if not os.path.exists(file_path):
            print(f"  ⚠️  Can't find {prefix}/{slug}")
            continue
        
        with open(file_path) as f:
            html = f.read()
        
        # Find body content
        if prefix == 'blog':
            body_start = html.find('<div class="article-body">')
            if body_start == -1:
                body_start = html.find('<article class="article-body">')
        else:
            # /a/blog/ uses <div class="article"> as the container
            body_start = html.find('<div class="article">')
            if body_start != -1:
                # Skip past the <h1> and <p class="post-lead"> to get to body content
                h1_pos = html.find('<h1>', body_start)
                lead_pos = html.find('</p>', body_start)
                if lead_pos == -1:
                    lead_pos = html.find('<h2>', body_start)
                if lead_pos != -1:
                    body_start = lead_pos + 4  # after </p>
        
        if body_start == -1:
            print(f"  ⚠️  Can't find body in {prefix}/{slug}")
            continue
        
        # Find where body ends - before further-reading, footer, post-cta
        body_end = html.find('<div class="further-reading', body_start)
        if body_end == -1:
            body_end = html.find('<div class="post-cta">', body_start)
        if body_end == -1:
            if prefix == 'blog':
                body_end = html.find('</footer>', body_start)
            else:
                body_end = html.find('<hr class="full-divider"/>', body_start)
        if body_end == -1:
            body_end = html.find('</div>', html.find('<!-- FOOTER', body_start))
            if body_end == -1:
                body_end = html.find('</article>', body_start)
        
        body_html = html[body_start:body_end]
        
        # Add links
        new_body, links_added = add_links_to_body(body_html, slug, prefix)
        
        if links_added > 0:
            html = html[:body_start] + new_body + html[body_end:]
            with open(file_path, 'w') as f:
                f.write(html)
            total_links += links_added
            print(f"  ✅ {prefix}/{slug}: +{links_added} links")
        else:
            print(f"  - {prefix}/{slug}: no new links found")
    
    return total_links


if __name__ == "__main__":
    total = 0
    for slug in ALL_SLUGS:
        print(f"\n🔗 {slug}...")
        n = process_post(slug)
        total += n
        if n:
            print(f"  Total so far: {total}")
    
    print(f"\n{'='*40}")
    print(f"✅ Added {total} cross-links total across {len(ALL_SLUGS)} slugs")
    
    # Commit
    subprocess.run(["git", "add", "blog/", "a/blog/"], cwd=REPO)
    result = subprocess.run(
        ["git", "commit", "-m", "Add contextual body cross-links to all GMS blog posts"],
        cwd=REPO, capture_output=True, text=True
    )
    print(result.stdout.strip())
    subprocess.run(["git", "push"], cwd=REPO)
    print("✅ Pushed to GitHub")
