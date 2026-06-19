def prompt_template_for_claude_api(input_data):
    json_output_format = """
        [
            {
                "feature_category": "Industry Intelligence",
                "sub_feature": "Sector, Geography, Trend Signals",
                "insight_summary": "Top-level macro + regional trends",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Social Media Intelligence",
                "sub_feature": "Official Profiles & Platform Activity",
                "insight_summary": "Platform links + summary of activity or themes",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Social Media Intelligence",
                "sub_feature": "Campaign Highlights",
                "insight_summary": "Post/campaign + format + engagement",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Social Media Intelligence",
                "sub_feature": "Hashtag/Keyword Insights",
                "insight_summary": "Top or rising hashtags in Industry/Region",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Social Media Intelligence",
                "sub_feature": "Engagement Rate Comparison",
                "insight_summary": "Carousel vs video vs reel performance for brands",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Content Strategy",
                "sub_feature": "Format Benchmarking",
                "insight_summary": "Top formats by engagement in Industry",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Content Strategy",
                "sub_feature": "Content Ideas Generator",
                "insight_summary": "10 content ideas for Brand Name on Content Pillars",
                "source_citation": ["Generated via AI, based on real content trends"]
            },
            {
                "feature_category": "Content Strategy",
                "sub_feature": "Influencer Recommendations",
                "insight_summary": "List of 10 relevant influencers with followers, Instagram username, region, niche",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Content Strategy",
                "sub_feature": "Emerging Influencer Detection",
                "insight_summary": "List of rising influencers in Region/Industry + growth metrics",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Content Strategy",
                "sub_feature": "Trending Audio",
                "insight_summary": "List of trending sounds/audio + use cases",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Competitor Intelligence",
                "sub_feature": "Competitor Activity & Benchmarking",
                "insight_summary": "Competitor campaigns, launches, performance",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Competitor Intelligence",
                "sub_feature": "Mentions & Media Presence",
                "insight_summary": "Where and how brands were mentioned",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Product Intelligence",
                "sub_feature": "Innovation Highlights",
                "insight_summary": "New products, formats, or feature releases in Industry",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Product Intelligence",
                "sub_feature": "Product Gap Analysis",
                "insight_summary": "Untapped segments or whitespace for Brand Name in Region",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Consumer Insights",
                "sub_feature": "Sentiment & Behavioral Patterns",
                "insight_summary": "Fan sentiment, feedback loops, or user reactions to brand/competitor posts",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Market Opportunities & Risks",
                "sub_feature": "Geo-signals & Emerging Risks",
                "insight_summary": "Market signals, growth spots, potential threats",
                "source_citation": ["Source 1", "Source 2"]
            }
        ]
        """

    base_prompt = f"""
        You are a senior market intelligence analyst with 25+ years of experience, tasked with generating a comprehensive, structured research report based on online content published from  {input_data.get('start_date')} to {input_data.get('end_date')} starting from the domain {input_data.get('website_url')}.

        Your objectives include:

        ---

        ### 🎯 Core Research Goals

        ### 1. Industry & Market Intelligence

        - Determine the primary sector and geographic focus of the brand.
        - Identify macro trends, market dynamics, and innovation signals within Industry.
        - Highlight geo-targeted or time-based shifts during the selected date range.

        ### 2. Social & Competitive Intelligence

        - Focus on these platforms (in order of priority): **Instagram, TikTok, YouTube, LinkedIn, Facebook, Pinterest**
        - Identify the official brand and competitor profiles and summarize their content activity.
        - Compare content format usage (e.g., carousels, videos, reels, shorts) and engagement.
        - Monitor major campaign launches, product drops, and content strategies.
        - Track high-performing hashtags, keywords, and earned media mentions.

        ### 3. Content Strategy Analysis

        - Benchmark top-performing content formats in Industry over the specified period.
        - Generate AI-powered content ideas for brand_name aligned with its content pillars (e.g., content_pillars).
        - Recommend relevant influencers (lifestyle, wellness, etc.) in region with follower stats and engagement.
        - Detect emerging creators in Industry/region with fast follower growth or viral activity.
        - If available, highlight **trending audio or sounds** used in high-engagement content.
        - Provide a **title and vivid description** for each **trending content pillar**.
        - Benchmark each trending content pillar and its performance against those of competitors.

        ### 4. Product Intelligence

        - List recent **product innovations** in Industry or by optional_competitors_name
        - Identify **product gaps or whitespace opportunities** for brand_name in region or globally.

        ### 5. Consumer Insights & Risk Mapping

        - Summarize public sentiment, fan reactions, and community trends around brand and category.
        - Identify growth opportunities or emerging threats, including regulatory/reputational risks.

        ### 🧾 Output Format: STRICTLY return ONLY a valid JSON list (no text before or after), where each item is a dictionary with the following structure.  

        {json_output_format}

        Each row should also include:

        - data_confidence: high, medium, or low
        - data_status: Updated, Partial, or Missing
        - source_type: platform_data, news_media, influencer_tools, community_forums, or brand_assets


        If no insights are found, fallback to:

        - data_status: "Missing"
        - insight_summary: "No data was surfaced for this category within the selected date range ({input_data.get('start_date')} – {input_data.get('end_date')})."


        ---

        ### 📌 Constraints & Instructions

        - Focus on {input_data.get('start_date')} to {input_data.get('end_date')} only.
        - Use only credible sources: news media, analytics platforms, verified brand accounts, platform APIs.
        - In "source_citation" return the **full URL to the exact article or data source**, not just the domain.

        ### Output Format Rules for `insight_summary`:

        - The value of `insight_summary` MUST be a JSON array of plain strings.
        - Each string must represent one distinct, self-contained insight.
        - If there are multiple insights, split them into **separate strings** in the array.
        - Do NOT wrap the strings in <cite> tags or any other markup.

        ⚠️ Escaping Rules:

        - If any string contains double quotes (e.g., quotes from campaign names or slogans), escape them properly as `\"`.
        - If a string contains backslashes (`\`), escape them as `\\`.
        - If a string includes line breaks, preserve them as `\\n` inside the string.
        - DO NOT use unescaped quotes inside any JSON string.


        ✅ Example:

        ```json
        "insight_summary": [
        "Brand launched the campaign titled \\\"The Future is Female\\\" targeting Gen Z professionals.",
        "Engagement was 3x higher on carousel formats compared to reels.",
        "Top-performing audio was \\\"Feel the Beat\\\" on Instagram Reels."
        ]

        OUTPUT FORMAT INSTRUCTIONS:

        - Return ONLY a valid JSON array of dictionaries matching this schema exactly:
        {{
            "feature_category": string,
            "sub_feature": string,
            "insight_summary": [string, ...],  
            "source_citation": [urls, ...],
            "data_confidence": "high" | "medium" | "low",
            "data_status": "Updated" | "Partial" | "Missing",
            "source_type": "platform_data" | "news_media" | "influencer_tools" | "community_forums" | "brand_assets"
        }}

        - Include ALL feature categories listed in the instructions, no omissions.
        - For missing data, set "data_status": "Missing" and insight_summary to ["No data was surfaced for this category within the selected date range"].
        - Each string in insight_summary must be properly escaped JSON strings (handle quotes, backslashes).
        - Do NOT add any text before or after the JSON array.

        Before returning JSON, output only: "CONFIRMED: ALL ENTRIES PRESENT"  
        Then immediately output the JSON array (no other text).
                    
        """
    
    return base_prompt


def prompt_template_for_perplexity_api(input_data):
    json_output_format = """
        [
            {
                "feature_category": "Industry Intelligence",
                "sub_feature": "Sector, Geography, Trend Signals",
                "insight_summary": "Top-level macro + regional trends",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Social Media Intelligence",
                "sub_feature": "Official Profiles & Platform Activity",
                "insight_summary": "Platform links + summary of activity or themes",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Social Media Intelligence",
                "sub_feature": "Campaign Highlights",
                "insight_summary": "Post/campaign + format + engagement",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Social Media Intelligence",
                "sub_feature": "Hashtag/Keyword Insights",
                "insight_summary": "Top or rising hashtags in Industry/Region",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Social Media Intelligence",
                "sub_feature": "Engagement Rate Comparison",
                "insight_summary": "Carousel vs video vs reel performance for brands",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Content Strategy",
                "sub_feature": "Format Benchmarking",
                "insight_summary": "Top formats by engagement in Industry",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Content Strategy",
                "sub_feature": "Content Ideas Generator",
                "insight_summary": "10 content ideas for Brand Name on Content Pillars",
                "source_citation": ["Generated via AI, based on real content trends"]
            },
            {
                "feature_category": "Content Strategy",
                "sub_feature": "Influencer Recommendations",
                "insight_summary": "List of 10 relevant influencers with followers, Instagram username, region, niche",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Content Strategy",
                "sub_feature": "Emerging Influencer Detection",
                "insight_summary": "List of rising influencers in Region/Industry + growth metrics",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Content Strategy",
                "sub_feature": "Trending Audio",
                "insight_summary": "List of trending sounds/audio + use cases",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Competitor Intelligence",
                "sub_feature": "Competitor Activity & Benchmarking",
                "insight_summary": "Competitor campaigns, launches, performance",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Competitor Intelligence",
                "sub_feature": "Mentions & Media Presence",
                "insight_summary": "Where and how brands were mentioned",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Product Intelligence",
                "sub_feature": "Innovation Highlights",
                "insight_summary": "New products, formats, or feature releases in Industry",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Product Intelligence",
                "sub_feature": "Product Gap Analysis",
                "insight_summary": "Untapped segments or whitespace for Brand Name in Region",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Consumer Insights",
                "sub_feature": "Sentiment & Behavioral Patterns",
                "insight_summary": "Fan sentiment, feedback loops, or user reactions to brand/competitor posts",
                "source_citation": ["Source 1", "Source 2"]
            },
            {
                "feature_category": "Market Opportunities & Risks",
                "sub_feature": "Geo-signals & Emerging Risks",
                "insight_summary": "Market signals, growth spots, potential threats",
                "source_citation": ["Source 1", "Source 2"]
            }
        ]
        """

    base_prompt = f"""
        You are a senior market intelligence analyst with 25+ years of experience, tasked with generating a comprehensive, structured research report based on online content published from  {input_data.get('start_date')} to {input_data.get('end_date')} starting from the domain {input_data.get('website_url')}.

        Your objectives include:

        ---

        ### 🎯 Core Research Goals

        ### 1. Industry & Market Intelligence

        - Determine the primary sector and geographic focus of the brand.
        - Identify macro trends, market dynamics, and innovation signals within Industry.
        - Highlight geo-targeted or time-based shifts during the selected date range.

        ### 2. Social & Competitive Intelligence

        - Focus on these platforms (in order of priority): **Instagram, TikTok, YouTube, LinkedIn, Facebook, Pinterest**
        - Identify the official brand and competitor profiles and summarize their content activity.
        - Compare content format usage (e.g., carousels, videos, reels, shorts) and engagement.
        - Monitor major campaign launches, product drops, and content strategies.
        - Track high-performing hashtags, keywords, and earned media mentions.

        ### 3. Content Strategy Analysis

        - Benchmark top-performing content formats in Industry over the specified period.
        - Generate AI-powered content ideas for brand_name aligned with its content pillars (e.g., content_pillars).
        - Recommend relevant influencers (lifestyle, wellness, etc.) in region with follower stats and engagement.
        - Detect emerging creators in Industry/region with fast follower growth or viral activity.
        - If available, highlight **trending audio or sounds** used in high-engagement content.
        - Provide a **title and vivid description** for each **trending content pillar**.
        - Benchmark each trending content pillar and its performance against those of competitors.

        ### 4. Product Intelligence

        - List recent **product innovations** in Industry or by optional_competitors_name
        - Identify **product gaps or whitespace opportunities** for brand_name in region or globally.

        ### 5. Consumer Insights & Risk Mapping

        - Summarize public sentiment, fan reactions, and community trends around brand and category.
        - Identify growth opportunities or emerging threats, including regulatory/reputational risks.

        ### 🧾 Output Format: STRICTLY return ONLY a valid JSON list (no text before or after), where each item is a dictionary with the following structure.  

        {json_output_format}

        Each row should also include:

        - data_confidence: high, medium, or low
        - data_status: Updated, Partial, or Missing
        - source_type: platform_data, news_media, influencer_tools, community_forums, or brand_assets


        If no insights are found, fallback to:

        - data_status: "Missing"
        - insight_summary: "No data was surfaced for this category within the selected date range ({input_data.get('start_date')} – {input_data.get('end_date')})."


        ---

        ### 📌 Constraints & Instructions

        - Focus on {input_data.get('start_date')} to {input_data.get('end_date')} only.
        - Use only credible sources: news media, analytics platforms, verified brand accounts, platform APIs.
        - In "source_citation" return the **full URL to the exact article or data source**, not just the domain.

        ### Output Format Rules for `insight_summary`:

        - The value of `insight_summary` MUST be a JSON array of plain strings.
        - Each string must represent one distinct, self-contained insight.
        - If there are multiple insights, split them into **separate strings** in the array.
        - Do NOT wrap the strings in <cite> tags or any other markup.

        ⚠️ Escaping Rules:

        - If any string contains double quotes (e.g., quotes from campaign names or slogans), escape them properly as `\"`.
        - If a string contains backslashes (`\`), escape them as `\\`.
        - If a string includes line breaks, preserve them as `\\n` inside the string.
        - DO NOT use unescaped quotes inside any JSON string.
        """
    
    return base_prompt
