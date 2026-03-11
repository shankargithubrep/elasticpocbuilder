from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List


class CreativeDataGenerator(DataGeneratorModule):
    """Data generator for Creative - Brand Asset Discovery"""

    @staticmethod
    def safe_choice(choices, size=None, weights=None, replace=True):
        """Safer alternative to np.random.choice with automatic probability normalization.

        Automatically handles complex elements (lists, tuples, dicts) by falling back
        to Python's random.choices when numpy would fail with shape errors.
        """
        use_python_random = False
        if len(choices) > 0:
            first_type = type(choices[0])
            if first_type in (list, tuple, dict):
                use_python_random = True

        if use_python_random:
            if size is None:
                if weights is not None:
                    return random.choices(choices, weights=weights, k=1)[0]
                else:
                    return random.choice(choices)
            if weights is not None:
                return random.choices(choices, weights=weights, k=size)
            else:
                return random.choices(choices, k=size)

        if weights is not None:
            weights = np.array(weights, dtype=float)
            if len(weights) > len(choices):
                import logging
                logging.warning(f"Truncating {len(weights) - len(choices)} excess weights")
                weights = weights[:len(choices)]
            elif len(weights) < len(choices):
                raise ValueError(
                    f"Not enough weights for choices!\n"
                    f"  Choices ({len(choices)}): {choices}\n"
                    f"  Weights ({len(weights)}): {weights.tolist()}"
                )
            probabilities = weights / weights.sum()
            if size is None:
                return np.random.choice(choices, p=probabilities, replace=replace)
            return np.random.choice(choices, size=size, p=probabilities, replace=replace)
        else:
            if size is None:
                return np.random.choice(choices)
            return np.random.choice(choices, size=size, replace=replace)

    @staticmethod
    def random_timedelta(start_date, end_date=None, days=None, hours=None, minutes=None, max_days=None):
        """Generate random timedelta-adjusted datetime, handling numpy int64 conversion.

        Usage patterns:
            random_timedelta(start, end)  # random datetime between start and end
            random_timedelta(datetime.now(), max_days=120)  # random datetime within last 120 days
            random_timedelta(base, days=5, hours=3)  # base + 5 days + 3 hours
        """
        if max_days is not None:
            # Random timestamp within last max_days days from start_date
            random_seconds = int(np.random.random() * int(max_days) * 86400)
            return start_date - timedelta(seconds=random_seconds)

        if end_date is not None:
            delta = end_date - start_date
            random_seconds = int(np.random.random() * delta.total_seconds())
            return start_date + timedelta(seconds=random_seconds)

        delta_kwargs = {}
        if days is not None:
            delta_kwargs['days'] = int(days)
        if hours is not None:
            delta_kwargs['hours'] = int(hours)
        if minutes is not None:
            delta_kwargs['minutes'] = int(minutes)

        return start_date + timedelta(**delta_kwargs)

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        """Generate datasets with EXACT fields from requirements"""
        datasets = {}

        datasets['brand_asset_catalog'] = self._generate_brand_asset_catalog()
        datasets['template_library'] = self._generate_template_library()
        datasets['visual_asset_embeddings'] = self._generate_visual_asset_embeddings()

        return datasets

    def _generate_brand_asset_catalog(self):
        """Generate brand_asset_catalog dataset"""
        import random
        from datetime import datetime

        n = 900

        # --- Asset IDs ---
        asset_ids = [f"BA-{str(100000 + i).zfill(6)}" for i in range(1, n + 1)]

        # --- Account IDs (50 distinct, skewed distribution) ---
        account_ids = [f"ACC-{1000 + i}" for i in range(1, 51)]
        # Skewed: a few accounts have many assets
        account_weights = []
        for i in range(50):
            if i < 5:
                account_weights.append(0.06)   # top 5 accounts: 6% each = 30%
            elif i < 15:
                account_weights.append(0.025)  # next 10: 2.5% each = 25%
            else:
                account_weights.append(0.0125) # remaining 35: ~1.25% each = 43.75%
        owner_account_ids = self.safe_choice(account_ids, size=n, weights=account_weights)

        # --- Business Verticals ---
        business_verticals = [
            "Food & Beverage", "Retail & E-commerce", "General Small Business",
            "Real Estate", "Fitness & Wellness", "Fashion & Apparel",
            "SaaS & Technology", "Hospitality", "Professional Services", "Healthcare & Beauty"
        ]
        bv_weights = [0.20, 0.15, 0.15, 0.08, 0.08, 0.08, 0.08, 0.07, 0.06, 0.05]
        business_vertical_col = self.safe_choice(business_verticals, size=n, weights=bv_weights)

        # --- Asset Types (18 distinct) ---
        asset_types = [
            "Logo", "Menu Board", "Social Media Graphic", "Email Template Header",
            "Promotional Banner", "Instagram Story Template", "Loyalty Card",
            "Product Photo", "Video Clip", "GIF Animation", "Flyer",
            "Business Card", "Signage", "Infographic", "Quote Graphic",
            "Event Poster", "Case Study Layout", "Class Schedule"
        ]
        at_weights = [0.10, 0.06, 0.10, 0.06, 0.10, 0.07, 0.06,
                      0.07, 0.05, 0.04, 0.06, 0.04, 0.05, 0.04,
                      0.04, 0.04, 0.03, 0.03]
        asset_type_col = self.safe_choice(asset_types, size=n, weights=at_weights)

        # --- Content Categories (12 distinct) ---
        content_categories = [
            "Brand Identity", "Food & Beverage Imagery", "Seasonal Promotion",
            "Social Media Content", "Email Marketing", "Product Showcase",
            "Customer Testimonial", "Event & Campaign", "Loyalty & Rewards",
            "Lifestyle & Editorial", "Business Operations", "Educational Content"
        ]
        cc_weights = [0.12, 0.10, 0.10, 0.12, 0.08, 0.09,
                      0.07, 0.08, 0.07, 0.07, 0.05, 0.05]
        content_category_col = self.safe_choice(content_categories, size=n, weights=cc_weights)

        # --- Campaign Themes (22 distinct) ---
        campaign_themes = [
            "Summer Promotion", "Holiday Sale", "Spring Collection", "Loyalty Program",
            "Italian Cuisine Feature", "Brand Refresh", "Customer Testimonial Campaign",
            "New Location Launch", "Back to School", "Valentine's Day Special",
            "Fall Harvest", "New Year New You", "Flash Sale", "Weekend Brunch Series",
            "Anniversary Celebration", "Product Launch", "Influencer Collab",
            "Community Spotlight", "Sustainability Initiative", "Winter Warmth",
            "Happy Hour Promo", "VIP Member Exclusive"
        ]
        ct_weights = [0.07, 0.07, 0.07, 0.07, 0.05, 0.05, 0.05,
                      0.05, 0.05, 0.04, 0.04, 0.04, 0.04, 0.04,
                      0.04, 0.04, 0.04, 0.04, 0.03, 0.04, 0.04, 0.04]
        campaign_theme_col = self.safe_choice(campaign_themes, size=n, weights=ct_weights)

        # --- Color Palette Tags (20 distinct, 1-3 per asset) ---
        all_palettes = [
            "warm-earth-tones", "bold-red-gold", "pastel-spring", "monochrome-black-white",
            "navy-gold-premium", "fresh-green-white", "sunset-orange-coral", "deep-burgundy-cream",
            "cool-blue-silver", "vibrant-tropical", "muted-sage-taupe", "electric-neon",
            "blush-rose-gold", "charcoal-white-minimal", "olive-terracotta", "sky-blue-white",
            "rich-chocolate-caramel", "lavender-lilac", "forest-green-gold", "bright-citrus-yellow"
        ]
        color_palette_tags_col = []
        for _ in range(n):
            num_tags = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
            chosen = random.sample(all_palettes, num_tags)
            color_palette_tags_col.append(chosen)

        # --- File Formats ---
        file_formats = ["PNG", "SVG", "JPEG", "MP4", "GIF", "PDF", "PSD", "AI"]
        ff_weights = [0.30, 0.15, 0.25, 0.08, 0.05, 0.10, 0.04, 0.03]
        file_format_col = self.safe_choice(file_formats, size=n, weights=ff_weights)

        # --- Aspect Ratios ---
        aspect_ratios = ["1:1", "16:9", "9:16", "4:5", "3:2", "2:3", "4:3", "1.91:1"]
        ar_weights = [0.25, 0.20, 0.20, 0.15, 0.10, 0.03, 0.04, 0.03]
        aspect_ratio_col = self.safe_choice(aspect_ratios, size=n, weights=ar_weights)

        # --- is_active (boolean, ~85% active) ---
        is_active_col = self.safe_choice([True, False], size=n, weights=[0.85, 0.15])

        # --- Upload Dates (within last 120 days) ---
        now = datetime.now()
        upload_dates = [self.random_timedelta(now, max_days=120).date() for _ in range(n)]

        # --- Reuse Count (lognormal skew: most low, some high) ---
        import numpy as np
        reuse_raw = np.random.lognormal(mean=1.8, sigma=1.2, size=n)
        reuse_count_col = np.clip(reuse_raw, 0, 500).astype(int)

        # --- Asset Titles ---
        biz_type_map = {
            "Food & Beverage": ["Coffee Shop", "Restaurant", "Bakery", "Pizzeria", "Cafe", "Italian Kitchen", "Sushi Bar", "Food Truck"],
            "Retail & E-commerce": ["Boutique", "Online Store", "Gift Shop", "Bookstore", "Electronics Shop", "Home Goods Store"],
            "General Small Business": ["Local Business", "Small Business", "Community Shop", "Neighborhood Store"],
            "Real Estate": ["Real Estate Agency", "Property Group", "Realty Firm", "Home Listings"],
            "Fitness & Wellness": ["Fitness Studio", "Yoga Studio", "Gym", "Wellness Center", "CrossFit Box"],
            "Fashion & Apparel": ["Fashion Brand", "Apparel Label", "Clothing Boutique", "Style Studio"],
            "SaaS & Technology": ["SaaS Platform", "Tech Startup", "Software Company", "App Brand"],
            "Hospitality": ["Hotel", "Resort", "Bed & Breakfast", "Vacation Rental"],
            "Professional Services": ["Law Firm", "Consulting Agency", "Accounting Firm", "Marketing Agency"],
            "Healthcare & Beauty": ["Spa", "Salon", "Wellness Clinic", "Beauty Studio"]
        }
        descriptor_map = {
            "Summer Promotion": ["Summer Vibes", "Summer Sale", "Hot Summer Deals", "Summer Refresh"],
            "Holiday Sale": ["Holiday Special", "Festive Sale", "Holiday Deals", "Season's Best"],
            "Spring Collection": ["Spring Bloom", "Spring Refresh", "Fresh Spring Looks", "Spring Awakening"],
            "Loyalty Program": ["Loyalty Rewards", "Member Benefits", "VIP Perks", "Rewards Program"],
            "Italian Cuisine Feature": ["Pasta Night", "Italian Flavors", "Authentic Italian", "Rustic Italian"],
            "Brand Refresh": ["New Look", "Brand Evolution", "Refreshed Identity", "Modern Rebrand"],
            "Customer Testimonial Campaign": ["Real Stories", "Customer Love", "Happy Clients", "Reviews & Praise"],
            "New Location Launch": ["Grand Opening", "Now Open", "New Location", "Opening Day"],
            "Back to School": ["Back to School", "School Season", "Study Season", "Campus Ready"],
            "Valentine's Day Special": ["Valentine's Love", "Valentine's Day", "Date Night Special", "Love & Romance"],
            "Fall Harvest": ["Fall Flavors", "Autumn Harvest", "Fall Collection", "Harvest Season"],
            "New Year New You": ["New Year Goals", "Fresh Start", "New Year Offer", "Resolution Ready"],
            "Flash Sale": ["Flash Deal", "Limited Time Offer", "Quick Sale", "Today Only"],
            "Weekend Brunch Series": ["Brunch Vibes", "Weekend Special", "Brunch Menu", "Sunday Brunch"],
            "Anniversary Celebration": ["Anniversary Special", "Celebrating Years", "Milestone Offer", "Anniversary Sale"],
            "Product Launch": ["New Arrival", "Just Launched", "Introducing", "Launch Day"],
            "Influencer Collab": ["Collab Drop", "Influencer Feature", "Creator Partnership", "Collab Launch"],
            "Community Spotlight": ["Community Love", "Local Heroes", "Spotlight Series", "Community Feature"],
            "Sustainability Initiative": ["Eco-Friendly", "Green Initiative", "Sustainable Choice", "Earth Friendly"],
            "Winter Warmth": ["Winter Cozy", "Warm Winter Deals", "Cold Weather Comfort", "Winter Warmup"],
            "Happy Hour Promo": ["Happy Hour", "Drink Specials", "After Work Deals", "Evening Special"],
            "VIP Member Exclusive": ["VIP Access", "Members Only", "Exclusive Offer", "Elite Perks"]
        }

        asset_titles = []
        for i in range(n):
            bv = business_vertical_col[i]
            at = asset_type_col[i]
            ct = campaign_theme_col[i]
            biz_options = biz_type_map.get(bv, ["Business"])
            biz = self.safe_choice(biz_options)
            desc_options = descriptor_map.get(ct, ["Special Offer", "Featured", "Seasonal"])
            desc = self.safe_choice(desc_options)
            title = f"{biz} {at} - {desc}"
            asset_titles.append(title)

        # --- Asset Descriptions (semantic_text, tiered, unique) ---
        tier1_templates = [
            ("This {at} is a core brand identity asset designed for {bv} businesses, featuring {cp} color palette. "
             "It includes logo variations and menu board layouts optimized for {ct} campaigns. "
             "The collateral supports food and beverage signage, loyalty program graphics, and Instagram story templates. "
             "Ideal for seasonal promotions including summer promotion and holiday sale contexts across digital and print channels."),
            ("A high-impact {at} built for {bv} marketing, showcasing Italian food and pasta imagery within a {cp} visual theme. "
             "This brand asset supports menu board design, restaurant dining collateral, and promotional banner placements. "
             "The asset includes logo variations aligned with the {ct} campaign and is suited for food and beverage imagery across social media graphic formats. "
             "Designed to drive engagement through loyalty program graphics and seasonal campaign messaging."),
            ("This {at} asset serves as a foundational piece of brand identity for {bv} operations running a {ct} initiative. "
             "Featuring a {cp} color scheme, it is optimized for Instagram story template use and social media graphic deployment. "
             "The design incorporates customer testimonial elements, discount badge overlays, and email template header formats. "
             "Supports multimodal content types including video clip and product photo integrations for omnichannel campaigns."),
            ("A versatile {at} crafted for {bv} businesses, this asset anchors the {ct} campaign with a bold {cp} aesthetic. "
             "It encompasses logo variations, loyalty card graphics, and promotional banner formats for both digital and physical signage. "
             "Coffee shop signage, modern kitchen imagery, and spring collection themes are woven into the visual identity. "
             "The asset supports email marketing, menu board display, and brand refresh initiatives simultaneously."),
            ("Designed as a flagship {at} for {bv} brands, this piece integrates brand identity principles with {ct} campaign goals. "
             "The {cp} palette reinforces seasonal promotion messaging including summer promotion and holiday sale themes. "
             "It includes quote graphic overlays, customer testimonial campaign visuals, and loyalty program badge elements. "
             "Optimized for Instagram story template dimensions and social media graphic repurposing across platforms.")
        ]
        tier2_templates = [
            ("This {at} was created to support {bv} marketing efforts during the {ct} campaign period. "
             "Using a {cp} visual style, the asset functions as promotional content across digital channels. "
             "The design balances brand materials with campaign-specific visual collateral, ensuring consistency across touchpoints. "
             "It is suitable for use in business signage, social content, and marketing graphics deployments."),
            ("A polished {at} asset tailored for {bv} use cases, aligned with the {ct} campaign narrative. "
             "The {cp} color treatment gives this marketing material a distinctive look that supports brand consistency. "
             "This promotional graphic works well as campaign collateral across email, web, and print environments. "
             "The visual identity elements have been refined to suit both digital-first and physical marketing contexts."),
            ("Built for {bv} brands executing a {ct} strategy, this {at} delivers clean visual collateral with a {cp} palette. "
             "The asset is structured to serve as adaptable brand material for multiple marketing channels. "
             "Campaign assets like this one are designed for reuse across promotional content cycles. "
             "The layout supports both static and animated deployment as a marketing graphic or business signage piece."),
            ("This {at} supports {bv} promotional content needs within the {ct} campaign framework. "
             "Rendered in a {cp} color scheme, it provides a flexible marketing graphic that adapts to various formats. "
             "The asset functions as visual collateral for social content, email campaigns, and physical display materials. "
             "Brand materials of this type are optimized for high reuse across seasonal and evergreen campaign cycles."),
            ("A campaign-ready {at} developed for {bv} businesses participating in {ct} initiatives. "
             "The {cp} palette drives visual cohesion across this suite of promotional content and brand materials. "
             "This marketing graphic is engineered for multi-channel deployment, from social content to email marketing assets. "
             "It reflects current design standards for business signage and digital visual collateral in competitive verticals.")
        ]
        tier3_templates = [
            ("This {at} is a general-purpose design template available for {bv} use cases. "
             "The {cp} color configuration was selected based on internal style guide recommendations. "
             "File metadata has been validated for compliance with platform upload standards. "
             "Administrative tagging reflects the {ct} campaign classification for archival purposes."),
            ("A standard {at} asset catalogued under the {bv} vertical for organizational reference. "
             "Color properties follow the {cp} specification noted during the asset intake process. "
             "This file was uploaded as part of a batch import and assigned to the {ct} campaign grouping. "
             "No additional design customization was applied beyond baseline template defaults."),
            ("Generic {at} template stored in the asset library for {bv} account holders. "
             "The {cp} palette designation was auto-assigned during the upload workflow. "
             "This asset is classified under {ct} for reporting and filtering purposes. "
             "Content has not been reviewed for active campaign deployment at this time."),
            ("An archived {at} resource associated with {bv} operations and the {ct} initiative. "
             "Color tagging reflects the {cp} palette used during the original design phase. "
             "This item is retained in the catalog for historical reference and potential future reuse. "
             "No active campaign deployment is currently scheduled for this asset."),
            ("This {at} represents a draft-stage design asset for {bv} stakeholders. "
             "The {cp} palette was specified in the creative brief but has not been finalized. "
             "It is catalogued under {ct} pending further review by the brand team. "
             "Metadata fields are populated for discoverability but content may require revision before use.")
        ]

        # Tier assignment: 20% T1, 40% T2, 40% T3
        tier_choices = self.safe_choice([1, 2, 3], size=n, weights=[0.20, 0.40, 0.40])

        asset_descriptions = []
        used_descriptions = set()

        for i in range(n):
            at = asset_type_col[i]
            bv = business_vertical_col[i]
            ct = campaign_theme_col[i]
            cp_list = color_palette_tags_col[i]
            cp = cp_list[0] if cp_list else "neutral"
            tier = tier_choices[i]

            if tier == 1:
                templates = tier1_templates
            elif tier == 2:
                templates = tier2_templates
            else:
                templates = tier3_templates

            # Try to get a unique description
            desc = None
            for attempt in range(10):
                tmpl = self.safe_choice(templates)
                candidate = tmpl.format(at=at, bv=bv, ct=ct, cp=cp)
                # Add uniqueness via a small suffix if collision
                if candidate not in used_descriptions:
                    desc = candidate
                    break
                else:
                    candidate = candidate + f" [Asset ref: {asset_ids[i]}]"
                    if candidate not in used_descriptions:
                        desc = candidate
                        break
            if desc is None:
                desc = (f"This {at} asset for {bv} supports the {ct} campaign with a {cp} palette. "
                        f"Unique reference: {asset_ids[i]}.")
            used_descriptions.add(desc)
            asset_descriptions.append(desc)

        return pd.DataFrame({
            "asset_id": asset_ids,
            "asset_title": asset_titles,
            "asset_description": asset_descriptions,
            "asset_type": asset_type_col,
            "content_category": content_category_col,
            "business_vertical": business_vertical_col,
            "campaign_theme": campaign_theme_col,
            "color_palette_tags": color_palette_tags_col,
            "file_format": file_format_col,
            "owner_account_id": owner_account_ids,
            "is_active": is_active_col,
            "upload_date": upload_dates,
            "reuse_count": reuse_count_col,
            "aspect_ratio": aspect_ratio_col,
        })

    def _generate_template_library(self):
        """Generate template_library dataset"""
        import numpy as np
        from datetime import datetime

        n = 900

        # --- Template ID ---
        template_ids = [f"TPL-{str(i).zfill(5)}" for i in np.random.choice(range(100, 9999), size=n, replace=False)]

        # --- Categories (12 distinct) ---
        categories = [
            "Social Media Post", "Email Newsletter", "Promotional Banner", "Menu & Signage",
            "Story & Reel", "Print Collateral", "Loyalty & Rewards", "Testimonial & Social Proof",
            "Product Showcase", "Event Announcement", "Campaign Landing Page", "Class & Schedule"
        ]
        cat_weights = [0.12, 0.11, 0.10, 0.08, 0.10, 0.07, 0.08, 0.08, 0.09, 0.07, 0.05, 0.05]
        template_categories = self.safe_choice(categories, size=n, weights=cat_weights)

        # --- Industry Tags (14 distinct) ---
        industries = [
            "Food & Beverage", "Coffee & Cafe", "Restaurant & Dining", "Retail & E-commerce",
            "Fashion & Apparel", "Fitness & Wellness", "Real Estate", "SaaS & Technology",
            "Beauty & Wellness", "Education & Coaching", "Health & Medical", "Travel & Hospitality",
            "Home & Interior", "Professional Services"
        ]
        ind_weights = [0.15, 0.10, 0.10, 0.12, 0.08, 0.08, 0.07, 0.06, 0.06, 0.05, 0.04, 0.04, 0.03, 0.02]
        industry_tags = self.safe_choice(industries, size=n, weights=ind_weights)

        # --- Campaign Types (16 distinct) ---
        campaign_types = [
            "Seasonal Promotion", "Product Launch", "Brand Awareness", "Customer Retention",
            "Holiday Campaign", "New Location Announcement", "Flash Sale", "Loyalty Program",
            "Event Promotion", "Referral Campaign", "Back to School", "Summer Sale",
            "Spring Collection", "Black Friday", "Grand Opening", "Community Engagement"
        ]
        camp_weights = [0.10, 0.08, 0.08, 0.07, 0.10, 0.05, 0.07, 0.07, 0.06, 0.05, 0.05, 0.06, 0.05, 0.05, 0.04, 0.02]
        campaign_type_arr = self.safe_choice(campaign_types, size=n, weights=camp_weights)

        # --- Platform Targets (12 distinct) ---
        platforms = [
            "Instagram Feed", "Instagram Story", "Facebook Post", "Facebook Ad",
            "Email Newsletter", "Google Display Ad", "Print / In-Store", "Pinterest",
            "Twitter / X", "LinkedIn", "TikTok", "YouTube Thumbnail"
        ]
        plat_weights = [0.18, 0.15, 0.12, 0.08, 0.15, 0.06, 0.07, 0.05, 0.04, 0.04, 0.04, 0.02]
        platform_targets = self.safe_choice(platforms, size=n, weights=plat_weights)

        # --- Customization Complexity ---
        complexities = ["Beginner", "Intermediate", "Advanced"]
        comp_weights = [0.45, 0.40, 0.15]
        customization_complexity = self.safe_choice(complexities, size=n, weights=comp_weights)

        # --- Is Premium (skewed: ~35% premium) ---
        is_premium = self.safe_choice([True, False], size=n, weights=[0.35, 0.65])

        # --- Popularity Score: beta distribution skewed toward mid-high ---
        raw_pop = np.random.beta(a=2.5, b=1.5, size=n)
        popularity_scores = np.round(raw_pop * 10.0, 2).clip(0.0, 10.0)

        # --- Last Updated: within last 120 days ---
        now = datetime.now()
        last_updated = [self.random_timedelta(now, max_days=120).strftime("%Y-%m-%d") for _ in range(n)]

        # --- Template Names ---
        industry_prefixes = {
            "Food & Beverage": ["Food & Beverage", "Gourmet", "Artisan Food"],
            "Coffee & Cafe": ["Coffee Shop", "Cafe", "Espresso Bar"],
            "Restaurant & Dining": ["Italian Restaurant", "Fine Dining", "Bistro"],
            "Retail & E-commerce": ["E-commerce", "Online Store", "Retail"],
            "Fashion & Apparel": ["Fashion", "Boutique", "Apparel"],
            "Fitness & Wellness": ["Fitness Studio", "Gym", "Wellness Center"],
            "Real Estate": ["Real Estate", "Property", "Realty"],
            "SaaS & Technology": ["SaaS", "Tech Startup", "Software"],
            "Beauty & Wellness": ["Beauty Salon", "Spa", "Skincare"],
            "Education & Coaching": ["Online Course", "Coaching", "Academy"],
            "Health & Medical": ["Healthcare", "Medical Practice", "Clinic"],
            "Travel & Hospitality": ["Travel Agency", "Hotel", "Resort"],
            "Home & Interior": ["Interior Design", "Home Decor", "Furniture"],
            "Professional Services": ["Consulting", "Agency", "Law Firm"],
        }
        platform_short = {
            "Instagram Feed": "Instagram", "Instagram Story": "Instagram Story",
            "Facebook Post": "Facebook", "Facebook Ad": "Facebook Ad",
            "Email Newsletter": "Email", "Google Display Ad": "Google Ads",
            "Print / In-Store": "Print", "Pinterest": "Pinterest",
            "Twitter / X": "Twitter", "LinkedIn": "LinkedIn",
            "TikTok": "TikTok", "YouTube Thumbnail": "YouTube",
        }
        content_type_map = {
            "Social Media Post": ["Post", "Graphic", "Visual"],
            "Email Newsletter": ["Newsletter", "Email Campaign", "Email Blast"],
            "Promotional Banner": ["Banner", "Promo Banner", "Ad Banner"],
            "Menu & Signage": ["Menu Board", "Signage", "Menu Layout"],
            "Story & Reel": ["Story", "Reel", "Short-Form Video"],
            "Print Collateral": ["Flyer", "Brochure", "Print Ad"],
            "Loyalty & Rewards": ["Loyalty Card", "Rewards Program", "Punch Card"],
            "Testimonial & Social Proof": ["Testimonial", "Quote Graphic", "Review Card"],
            "Product Showcase": ["Product Post", "Showcase", "Catalog"],
            "Event Announcement": ["Event Flyer", "Announcement", "Invite"],
            "Campaign Landing Page": ["Landing Page", "Campaign Page", "Promo Page"],
            "Class & Schedule": ["Class Schedule", "Timetable", "Schedule Board"],
        }
        descriptors = ["Seasonal", "Minimal", "Bold", "Elegant", "Playful", "Modern", "Classic", "Vibrant", "Clean", "Dynamic"]

        template_names = []
        for i in range(n):
            ind = industry_tags[i]
            cat = template_categories[i]
            plat = platform_targets[i]
            prefix_list = industry_prefixes.get(ind, ["Business"])
            prefix = self.safe_choice(prefix_list)
            plat_label = platform_short.get(plat, plat)
            ct_list = content_type_map.get(cat, ["Template"])
            ct = self.safe_choice(ct_list)
            desc = self.safe_choice(descriptors)
            template_names.append(f"{prefix} {plat_label} {ct} - {desc}")

        # --- Template Descriptions (tiered, unique, coherent) ---
        tier1_templates = [
            (
                "A ready-to-use {category} designed specifically for {industry} businesses running a {campaign} campaign on {platform}. "
                "This menu board layout features bold typography and high-contrast color blocks to showcase daily specials and seasonal offerings. "
                "Perfect for Italian restaurants and food and beverage brands, this template supports full customization of fonts, colors, and imagery. "
                "Ideal for small business marketing efforts targeting in-store customers and social media audiences simultaneously. "
                "Swap in your logo, update pricing, and publish in minutes with no design experience required."
            ),
            (
                "This Instagram story template is built for {industry} brands launching a {campaign} on {platform}. "
                "Featuring a vibrant summer promotion layout with animated-style overlays and bold call-to-action buttons, "
                "this design framework helps coffee shops and cafes drive foot traffic during seasonal peaks. "
                "The template supports easy text swaps, color palette adjustments, and logo placement for seamless brand identity integration. "
                "A go-to creative scaffold for seasonal marketing and holiday sale promotions targeting mobile-first audiences."
            ),
            (
                "Crafted for {industry} brands, this {category} is optimized for {platform} and supports {campaign} initiatives. "
                "This email campaign template features a loyalty program design with reward tier callouts, personalized greeting blocks, and promotional banner sections. "
                "Coffee shop and restaurant brands can highlight their loyalty card offers, punch card milestones, and exclusive member discounts. "
                "The layout is structured for high open-rate email newsletters with a clean hierarchy and scannable sections. "
                "Customize colors, swap product images, and update copy to match your seasonal email calendar."
            ),
            (
                "A holiday sale template purpose-built for {industry} businesses running {campaign} campaigns on {platform}. "
                "This promotional banner design uses festive color gradients, countdown-style urgency elements, and discount badge placements. "
                "Retail and e-commerce brands can quickly adapt this layout for Black Friday, holiday season, or flash sale events. "
                "The {category} format ensures visual consistency across digital and print channels. "
                "Designed for small business marketing teams with beginner-level customization complexity."
            ),
            (
                "This customer testimonial graphic template is designed for {industry} companies seeking social proof on {platform}. "
                "The quote template layout features a clean card-style design with avatar placeholders, star rating badges, and brand color accents. "
                "SaaS and technology brands can use this {category} to showcase client success stories as part of a {campaign} strategy. "
                "Each element is fully editable, making it easy to refresh testimonials weekly without redesigning from scratch. "
                "A powerful tool for building brand trust and credibility through authentic customer voices."
            ),
            (
                "Built for {industry} studios and gyms, this class schedule template is optimized for {platform} and {campaign} use cases. "
                "The fitness studio layout includes a weekly timetable grid, instructor name fields, class type icons, and session duration indicators. "
                "This {category} design makes it simple to publish your schedule to Instagram Story or print it for in-store display. "
                "Color-coded class categories and bold header typography ensure readability at a glance. "
                "Update session details in minutes and maintain consistent branding across all your fitness marketing channels."
            ),
            (
                "A real estate listing description template tailored for {industry} agents running {campaign} campaigns on {platform}. "
                "This {category} features a modern kitchen showcase layout with virtual tour call-to-action buttons, property highlight badges, and agent contact blocks. "
                "Designed for Instagram Feed and Facebook Ad placements, this template helps realtors present listings with professional polish. "
                "The listing description format supports MLS data integration placeholders and neighborhood highlight sections. "
                "Ideal for agents looking to elevate their social media graphic game without hiring a designer."
            ),
            (
                "This spring collection template is designed for {industry} boutiques and fashion brands running {campaign} promotions on {platform}. "
                "The e-commerce product showcase layout features a clean white-space grid, lifestyle imagery placeholders, and seasonal color palette swatches. "
                "Perfect for Instagram Feed posts and Pinterest boards, this {category} drives product discovery and click-through for new arrivals. "
                "The design framework supports up to six product tiles with individual price and description fields. "
                "A must-have seasonal marketing asset for fashion and apparel brands refreshing their visual identity each season."
            ),
        ]

        tier2_templates = [
            (
                "This {category} provides a versatile marketing layout for {industry} brands executing {campaign} strategies on {platform}. "
                "The promotional design framework includes modular content blocks, placeholder imagery zones, and adaptable color themes. "
                "Social content scaffolds like this one help marketing teams maintain visual consistency across multiple campaign touchpoints. "
                "The digital marketing material is structured for quick turnaround, enabling teams to produce polished assets without extensive design resources. "
                "Suitable for brands at any stage of their visual identity journey."
            ),
            (
                "A campaign visual system built for {industry} marketers targeting {platform} audiences with {campaign} messaging. "
                "This {category} offers a flexible grid structure with interchangeable headline, subheadline, and CTA button placements. "
                "The marketing format supports both portrait and landscape orientations, making it adaptable for multi-platform rollouts. "
                "Teams can use this promotional design framework as a base for A/B testing different visual approaches within the same campaign. "
                "Comes with pre-set font pairings and a curated color palette aligned with current design trends."
            ),
            (
                "Designed for {industry} teams, this {category} serves as a social content scaffold for {campaign} activations on {platform}. "
                "The layout features a clean typographic hierarchy, brand logo zone, and flexible image container that adapts to various aspect ratios. "
                "Marketing teams can use this digital marketing material to streamline their content production pipeline and reduce design bottlenecks. "
                "The template includes guidance annotations to help non-designers make confident customization decisions. "
                "A reliable foundation for any {industry} brand building out their content library."
            ),
            (
                "This {platform}-optimized {category} is tailored for {industry} brands running {campaign} initiatives. "
                "The marketing layout includes a featured content zone, supporting text area, and branded footer with social handle placeholders. "
                "Visual systems like this one help small business marketing teams produce professional-grade assets at scale. "
                "The design is intentionally minimal to keep the focus on your core message and call to action. "
                "Easily adaptable for both digital and print applications with minor sizing adjustments."
            ),
            (
                "A promotional design framework for {industry} businesses launching {campaign} content on {platform}. "
                "This {category} uses a bold color-blocking technique to create visual hierarchy and draw attention to key offers. "
                "The campaign visual system includes editable headline layers, supporting copy fields, and a prominent CTA button zone. "
                "Ideal for marketing teams looking to maintain brand consistency while producing high volumes of campaign assets quickly. "
                "The template is compatible with popular design tools and requires no advanced design skills to customize effectively."
            ),
            (
                "This {category} is a social content scaffold designed for {industry} brands pursuing {campaign} goals on {platform}. "
                "The marketing format features a dual-column layout with an image panel and a text panel, creating a balanced visual composition. "
                "Brand teams can swap imagery, update copy, and adjust color themes to align with seasonal campaigns or product launches. "
                "The digital marketing material includes pre-built text styles to ensure typographic consistency across all brand touchpoints. "
                "A dependable creative scaffold for teams that need to move fast without sacrificing quality."
            ),
            (
                "Built for {industry} marketers, this {campaign} focused {category} delivers a clean and adaptable design for {platform}. "
                "The promotional banner layout uses a layered design approach with background imagery, overlay gradients, and foreground text elements. "
                "This marketing layout is engineered for high visual impact in crowded social media feeds and inbox previews. "
                "Teams can customize the color palette, swap headline copy, and reposition the CTA to match specific campaign objectives. "
                "A versatile addition to any brand's digital marketing material library."
            ),
            (
                "This {platform} {category} is optimized for {industry} teams running {campaign} content at scale. "
                "The campaign visual system features a modular card design that can be adapted for individual posts or carousel sequences. "
                "Marketing teams appreciate the clear placeholder structure that makes onboarding new designers straightforward. "
                "The social content scaffold includes optional badge and icon layers for highlighting promotions, new arrivals, or limited-time offers. "
                "A solid marketing format for brands that prioritize consistency and speed in their content operations."
            ),
            (
                "A flexible {category} designed for {industry} brands executing {campaign} campaigns across {platform}. "
                "This promotional design framework emphasizes clean white space, strong typographic anchors, and a single focal image zone. "
                "The marketing layout is built to communicate one clear message efficiently, making it ideal for time-sensitive campaigns. "
                "Brand teams can layer in seasonal color accents or swap imagery to keep the template feeling fresh across multiple uses. "
                "An essential digital marketing material for brands that value simplicity and clarity in their visual communications."
            ),
            (
                "This {category} serves as a campaign visual system for {industry} businesses targeting {platform} with {campaign} content. "
                "The design framework features a headline-first layout with supporting visual elements that complement rather than compete with the core message. "
                "Marketing teams can use this social content scaffold as a starting point for both evergreen and campaign-specific content. "
                "The template includes color and font customization zones clearly marked for easy editing by non-designers. "
                "A reliable promotional design framework for brands building out their content calendar efficiently."
            ),
        ]

        tier3_templates = [
            (
                "A general-purpose {category} suitable for {industry} organizations with basic content needs on {platform}. "
                "This template provides a standard grid layout with placeholder zones for text and imagery. "
                "The design is intentionally neutral to support a wide range of {campaign} use cases without heavy customization. "
                "Teams can apply their brand colors and fonts to adapt this template to their specific communication requirements. "
                "A functional starting point for organizations exploring digital content creation for the first time."
            ),
            (
                "This {category} offers a generic layout framework for {industry} teams working on {campaign} projects targeting {platform}. "
                "The template features a standard two-column grid with header and footer zones suitable for various content types. "
                "No specialized design knowledge is required to populate this template with relevant content. "
                "The abstract design system can be adapted for internal communications, external marketing, or hybrid use cases. "
                "A versatile base template for organizations that need a quick starting point without a specific visual direction."
            ),
            (
                "A corporate-style {category} designed for {industry} teams managing {campaign} content on {platform}. "
                "This template features a formal layout with structured content zones, a neutral color palette, and professional typography. "
                "The design is optimized for clarity and readability rather than visual impact, making it suitable for informational content. "
                "Teams can customize the header branding, adjust the color scheme, and populate the content zones with relevant information. "
                "A reliable template for organizations that prioritize clear communication over design flair."
            ),
            (
                "This abstract {category} provides a flexible design scaffold for {industry} organizations running {campaign} initiatives on {platform}. "
                "The template uses a geometric pattern background with overlaid content zones for text and imagery. "
                "The design aesthetic is modern and minimal, suitable for a wide range of business contexts and communication needs. "
                "Teams can adapt the color palette and typography to align with their existing brand guidelines. "
                "A general-purpose template that works across multiple industries and content types without significant modification."
            ),
            (
                "A standard {category} layout for {industry} teams producing {campaign} content for {platform} distribution. "
                "This template provides a clean, uncluttered canvas with clearly defined zones for headlines, body copy, and visual elements. "
                "The design prioritizes functional clarity over decorative elements, making it easy to populate with varied content types. "
                "Brand teams can apply custom colors, fonts, and imagery to transform this generic scaffold into a branded asset. "
                "Suitable for organizations at any stage of their content marketing journey."
            ),
            (
                "This {category} is a basic design framework for {industry} organizations exploring {campaign} content on {platform}. "
                "The template features a single-column layout with stacked content blocks for headlines, images, and body text. "
                "The minimal structure makes this template highly adaptable for a variety of content formats and communication objectives. "
                "Teams can use this as a starting point and build complexity incrementally as their design capabilities grow. "
                "A foundational template for organizations beginning their digital content creation journey."
            ),
            (
                "A generic {category} template designed for {industry} teams working on {campaign} projects for {platform}. "
                "The layout features a neutral design system with interchangeable content modules and a flexible grid structure. "
                "This template is intentionally designed to be industry-agnostic, making it suitable for a wide range of business contexts. "
                "Teams can apply brand-specific elements to personalize the design without altering the underlying structure. "
                "A practical starting point for organizations that need a quick, functional template without a specific creative direction."
            ),
            (
                "This {platform}-ready {category} provides a simple design framework for {industry} teams running {campaign} content. "
                "The template uses a standard layout with header, body, and footer zones that can be populated with any content type. "
                "The design is clean and functional, prioritizing ease of use over visual complexity. "
                "Teams with limited design resources will find this template easy to customize and deploy quickly. "
                "A reliable fallback template for organizations that need a polished output with minimal design effort."
            ),
            (
                "A straightforward {category} for {industry} organizations managing {campaign} communications on {platform}. "
                "This template features an HR-communication-inspired layout with clear section dividers, bullet-point friendly text zones, and a professional header. "
                "The design system is optimized for information density rather than visual storytelling, making it ideal for data-heavy content. "
                "Teams can customize the section headers, adjust the color scheme, and populate the content zones with relevant information. "
                "A practical template for organizations that need to communicate complex information clearly and efficiently."
            ),
            (
                "This {category} offers a minimal design scaffold for {industry} teams producing {campaign} assets for {platform}. "
                "The template features a clean white background with subtle accent colors and a structured content hierarchy. "
                "The design is intentionally understated to allow the content to take center stage without visual distractions. "
                "Teams can apply their brand palette and typography to align this template with their existing visual identity. "
                "A versatile, low-complexity template suitable for a wide range of business communication needs."
            ),
        ]

        # Assign tiers: 20% tier1, 40% tier2, 40% tier3
        tier_assignments = self.safe_choice([1, 2, 3], size=n, weights=[0.20, 0.40, 0.40])

        template_descriptions = []
        t1_idx = 0
        t2_idx = 0
        t3_idx = 0

        for i in range(n):
            cat = template_categories[i]
            ind = industry_tags[i]
            camp = campaign_type_arr[i]
            plat = platform_targets[i]
            tier = tier_assignments[i]

            fmt_kwargs = {
                "category": cat,
                "industry": ind,
                "campaign": camp,
                "platform": plat,
            }

            if tier == 1:
                template_str = tier1_templates[t1_idx % len(tier1_templates)]
                t1_idx += 1
            elif tier == 2:
                template_str = tier2_templates[t2_idx % len(tier2_templates)]
                t2_idx += 1
            else:
                template_str = tier3_templates[t3_idx % len(tier3_templates)]
                t3_idx += 1

            desc = template_str.format(**fmt_kwargs)
            # Make unique by appending row-specific suffix
            desc = desc + f" [Template #{i+1} | {ind} | {plat}]"
            template_descriptions.append(desc)

        return pd.DataFrame({
            "template_id": template_ids,
            "template_name": template_names,
            "template_description": template_descriptions,
            "template_category": template_categories,
            "industry_tag": industry_tags,
            "campaign_type": campaign_type_arr,
            "platform_target": platform_targets,
            "customization_complexity": customization_complexity,
            "is_premium": is_premium,
            "popularity_score": popularity_scores,
            "last_updated": last_updated,
        })

    def _generate_visual_asset_embeddings(self):
        """Generate visual_asset_embeddings dataset"""
        import numpy as np
        from datetime import datetime

        n = 900  # Medium preference within 500-1500 range

        # --- Embedding IDs (sequential, unique) ---
        start_id = 10042
        embedding_ids = [f"EMB-{start_id + i:05d}" for i in range(n)]

        # --- Source asset IDs (400 distinct, some assets have 2-3 embeddings) ---
        base_asset_nums = np.random.randint(1000, 9000, size=400)
        source_asset_pool = [f"BA-{str(num).zfill(6)}" for num in base_asset_nums]
        # Weighted: ~60% single embedding, ~30% double, ~10% triple
        asset_weights = np.random.choice([1, 2, 3], size=400, p=[0.60, 0.30, 0.10])
        expanded_pool = []
        for asset_id, weight in zip(source_asset_pool, asset_weights):
            expanded_pool.extend([asset_id] * weight)
        # Sample n from expanded pool
        if len(expanded_pool) < n:
            expanded_pool = expanded_pool * (n // len(expanded_pool) + 2)
        source_asset_ids = [expanded_pool[i % len(expanded_pool)] for i in range(n)]

        # --- Owner account IDs (50 distinct) ---
        account_nums = [1001, 1042, 1187, 1256, 1334, 1412, 1578, 1690,
                        1723, 1845, 1902, 1967, 2034, 2112, 2289, 2345,
                        2401, 2567, 2634, 2712, 2801, 2934, 3012, 3089,
                        3134, 3278, 3345, 3412, 3567, 3634, 3712, 3845,
                        3901, 4023, 4112, 4234, 4312, 4467, 4534, 4612,
                        4734, 4812, 4934, 5012, 5134, 5212, 5334, 5467,
                        5534, 5678]
        account_pool = [f"ACC-{num}" for num in account_nums]
        # Skewed: some accounts own many more assets (lognormal-like weighting)
        raw_weights = np.random.lognormal(mean=0, sigma=1.2, size=50)
        raw_weights = raw_weights / raw_weights.sum()
        owner_account_ids = self.safe_choice(account_pool, size=n, weights=raw_weights.tolist())

        # --- Embedding model versions (weighted) ---
        model_versions = [
            "clip-vit-large-patch14-v1",
            "clip-vit-base-patch32-v2",
            "openai-ada-002-multimodal",
            "google-multimodal-embed-v1",
            "elastic-elser-v2-visual"
        ]
        model_weights = [0.40, 0.30, 0.15, 0.10, 0.05]
        embedding_model_versions = self.safe_choice(model_versions, size=n, weights=model_weights)

        # --- Modality (weighted) ---
        modalities_list = ["image", "graphic-design", "logo-vector", "video-frame", "document-visual"]
        modality_weights = [0.40, 0.30, 0.12, 0.10, 0.08]
        modalities = self.safe_choice(modalities_list, size=n, weights=modality_weights)

        # --- Asset ref titles ---
        visual_subjects = [
            "Espresso Bar Setup", "Pasta Dish Plated", "Summer Sale Window Display",
            "Modern Kitchen Interior", "Fitness Class Action Shot", "Spring Fashion Flatlay",
            "Customer Smiling Testimonial", "Holiday Gift Display", "Coffee Cup Close-Up",
            "Italian Food Spread", "Menu Board Layout", "Logo Variations Sheet",
            "Loyalty Card Design", "Instagram Story Template", "Promotional Banner",
            "Discount Badge Graphic", "Salad Bowl Overhead", "Boutique Storefront",
            "Apparel Product Flatlay", "Brand Identity Collateral", "Class Schedule Poster",
            "Seasonal Campaign Visual", "Restaurant Dining Scene", "Coffee Shop Signage",
            "Email Header Graphic", "Case Study Visual", "Property Photo Exterior",
            "Virtual Tour Still", "Quote Graphic Social Proof", "Spring Collection Lookbook"
        ]
        style_descriptors = [
            "Vibrant", "Minimal", "Rustic", "Editorial", "Lifestyle",
            "Product-Focused", "Candid", "Branded", "Bold", "Warm",
            "Clean", "Artisan", "Dynamic", "Soft", "Saturated"
        ]
        asset_type_refs = [
            "Photo", "Graphic", "Illustration", "Video Still", "Logo Lockup",
            "Banner", "Template", "Poster", "Badge", "Collateral"
        ]

        asset_ref_titles = []
        for i in range(n):
            subj = self.safe_choice(visual_subjects)
            style = self.safe_choice(style_descriptors)
            asset_type = self.safe_choice(asset_type_refs)
            title = f"{subj} - {style} {asset_type}"
            asset_ref_titles.append(title)

        # --- Capture dates ---
        now = datetime.now()
        capture_dates = [self.random_timedelta(now, max_days=120).strftime("%Y-%m-%d") for _ in range(n)]

        # --- Visual captions (tiered, unique) ---
        tier1_templates = [
            ("This image depicts three logo variations for a coffee shop brand, featuring the primary wordmark, "
             "a circular badge version, and a simplified icon lockup, all rendered in warm earth tones suitable "
             "for menu boards and loyalty cards. The {modality} asset showcases the brand identity collateral "
             "in a clean layout ideal for discovery across digital and print channels. Referenced asset: {title}."),
            ("This {modality} captures a richly styled Italian food spread featuring handmade pasta dish plated "
             "with fresh herbs and parmesan, shot in a rustic editorial style for restaurant dining promotions. "
             "The food photography highlights warm tones and texture, making it ideal for menu board and "
             "social media use. Asset reference: {title}."),
            ("A vibrant promotional banner graphic for a summer promotion campaign, featuring bold typography, "
             "a discount badge overlay, and lifestyle imagery of a coffee shop storefront. This {modality} "
             "is designed as an Instagram story template and email header graphic for seasonal campaign use. "
             "See also: {title}."),
            ("This {modality} presents a loyalty program graphic featuring a loyalty card design with brand "
             "identity elements, color palette swatches, and a logo lockup. The asset is intended for "
             "point-of-sale signage and digital loyalty program collateral. Asset: {title}."),
            ("A crisp product photo of an espresso cup on a marble surface, captured in a product-focused "
             "style for e-commerce imagery and promotional graphic use. This {modality} highlights the "
             "coffee shop aesthetic with clean composition and warm lighting. Reference: {title}."),
            ("This {modality} showcases a class schedule poster for a fitness studio, featuring action shots "
             "of a fitness class in session with dynamic typography and branded color overlays. Suitable for "
             "Instagram story templates and in-studio signage. Asset title: {title}."),
            ("A spring collection lookbook flatlay featuring boutique apparel laid out in an editorial style, "
             "with pastel color palette and soft natural lighting. This {modality} serves as a fashion photo "
             "for seasonal campaign and social proof content. Referenced: {title}."),
            ("This {modality} depicts a customer testimonial quote graphic with a candid customer smiling "
             "portrait, overlaid with branded typography and social proof messaging. Designed for Instagram "
             "story and promotional banner use. Asset: {title}."),
            ("A holiday gift display photo featuring curated product arrangements with holiday sale signage "
             "and branded ribbon elements. This {modality} is a seasonal campaign visual for email header "
             "graphics and point-of-sale displays. Title: {title}."),
            ("This {modality} presents a modern kitchen interior property photo with clean lines, natural "
             "light, and lifestyle staging. The image serves as a virtual tour still and brand identity "
             "collateral for real estate and hospitality marketing. Reference: {title}.")
        ]

        tier2_templates = [
            ("This {modality} features culinary imagery of a plated salad bowl captured overhead with "
             "natural lighting and artisan styling, suitable for use in campaign visual content and "
             "point-of-sale signage across restaurant channels. Asset reference: {title}."),
            ("A visual identity collateral piece featuring logo lockup variations and color palette "
             "swatches rendered as a {modality} for brand discovery and asset management workflows. "
             "The layout supports multi-channel deployment. Title: {title}."),
            ("This {modality} showcases lifestyle imagery from a boutique storefront environment, "
             "capturing the ambiance and apparel display in a warm, branded editorial style. "
             "Suitable for seasonal campaign and social media use. Referenced asset: {title}."),
            ("A document-style {modality} presenting a menu layout with typography hierarchy, "
             "food category icons, and brand color palette. The asset supports point-of-sale "
             "and digital menu board deployment. Asset: {title}."),
            ("This {modality} captures a video still from a fitness studio workout session, "
             "featuring dynamic motion and branded overlay graphics for social media and "
             "promotional banner applications. Reference: {title}."),
            ("A graphic-design {modality} featuring a spring collection promotional banner "
             "with pastel tones, floral motifs, and discount badge elements for e-commerce "
             "and email marketing campaigns. Title: {title}."),
            ("This {modality} presents a case study visual with data visualization overlays "
             "and branded typography, serving as visual identity collateral for B2B marketing "
             "and client presentation decks. Asset reference: {title}."),
            ("A logo-vector {modality} featuring a simplified icon lockup for a coffee brand, "
             "rendered in scalable format for use across coffee shop signage, loyalty cards, "
             "and digital brand identity applications. Title: {title}."),
            ("This {modality} depicts a promotional graphic for a holiday sale event, featuring "
             "gift imagery, seasonal typography, and a discount badge overlay for email header "
             "and social media use. Asset: {title}."),
            ("A lifestyle {modality} capturing a customer testimonial scene in a coffee shop "
             "setting, with warm ambient lighting and branded environmental signage visible "
             "in the background. Reference: {title}."),
            ("This {modality} showcases an Instagram story template design with bold geometric "
             "frames, brand color palette, and placeholder text zones for campaign visual "
             "content deployment. Title: {title}."),
            ("A product-focused {modality} featuring an espresso bar setup with branded cups, "
             "equipment, and menu board visible in the background, shot for coffee shop "
             "marketing and hospitality brand discovery. Asset: {title}."),
            ("This {modality} presents a spring fashion flatlay with apparel items arranged "
             "in a minimal editorial style, featuring color-coordinated accessories and "
             "seasonal campaign visual content framing. Reference: {title}."),
            ("A {modality} depicting a restaurant dining scene with Italian food spread, "
             "ambient candlelight, and rustic table styling for use in food photography "
             "and seasonal campaign collateral. Title: {title}."),
            ("This {modality} features a loyalty program graphic with loyalty card design "
             "elements, QR code placeholder, and brand wordmark, suitable for print and "
             "digital loyalty program deployment. Asset reference: {title}.")
        ]

        tier3_templates = [
            ("This {modality} presents an abstract geometric pattern in muted blue and grey tones, "
             "generated as a background texture asset for general design library use. "
             "The composition features repeating hexagonal shapes with subtle gradient overlays. "
             "Asset title: {title}."),
            ("A stock photo depicting a generic open-plan office environment with natural light, "
             "collaborative workspaces, and unbranded technology equipment visible throughout. "
             "This {modality} serves as a background asset for corporate presentations. Title: {title}."),
            ("This {modality} captures an architectural diagram of a commercial building facade, "
             "rendered in technical line-art style with dimension annotations and material callouts. "
             "Intended for construction project documentation. Reference: {title}."),
            ("A nature photography {modality} featuring a mountain landscape at golden hour, "
             "with wide-angle composition and atmospheric haze effects. The image serves as a "
             "generic stock visual for travel and wellness content. Asset: {title}."),
            ("This {modality} depicts a data dashboard screenshot with bar charts, pie graphs, "
             "and KPI metric cards in a SaaS analytics interface. The visual is used for "
             "software product documentation and UI design reference. Title: {title}."),
            ("A technical illustration {modality} showing a cross-section diagram of an HVAC "
             "system installation, with labeled components and airflow direction arrows. "
             "Created for engineering documentation purposes. Reference: {title}."),
            ("This {modality} presents a flat-lay photograph of office stationery items including "
             "notebooks, pens, and sticky notes arranged on a white surface. Generic business "
             "lifestyle imagery for unspecified corporate use. Asset: {title}."),
            ("A {modality} featuring a watercolor texture background in soft pastel tones, "
             "created as a decorative design element for greeting card and invitation templates. "
             "No brand-specific content is present. Title: {title}."),
            ("This {modality} captures a bird's-eye aerial photograph of a suburban neighborhood "
             "taken during daylight hours, showing residential streets and green spaces. "
             "Intended for urban planning and real estate overview use. Reference: {title}."),
            ("A {modality} depicting a scientific infographic about cellular biology, featuring "
             "labeled diagrams of cell structures and process flow annotations. Created for "
             "educational content and medical publication use. Asset: {title}."),
            ("This {modality} presents a vintage-style map illustration of a fictional city, "
             "rendered with hand-drawn cartographic elements and aged parchment texture. "
             "Used as a decorative asset for themed events. Title: {title}."),
            ("A {modality} featuring a time-lapse video still of a busy urban intersection "
             "with light trails from passing vehicles captured at night. Generic urban "
             "lifestyle content for unspecified editorial use. Reference: {title}."),
            ("This {modality} shows a macro photograph of a circuit board with electronic "
             "components highlighted under studio lighting. Intended for technology product "
             "documentation and hardware marketing collateral. Asset: {title}."),
            ("A {modality} depicting a children's book illustration style artwork featuring "
             "cartoon animals in a forest setting, rendered in bright primary colors. "
             "Created for educational publishing and youth content. Title: {title}."),
            ("This {modality} presents a minimalist black-and-white portrait photograph of "
             "an unidentified person in profile view, shot in a studio setting with dramatic "
             "side lighting. Generic editorial portrait for unspecified use. Reference: {title}.")
        ]

        # Tier distribution: 20% tier1, 40% tier2, 40% tier3
        tier_choices = self.safe_choice([1, 2, 3], size=n, weights=[0.20, 0.40, 0.40])

        visual_captions = []
        used_captions = set()

        for i in range(n):
            tier = tier_choices[i]
            modality_val = modalities[i]
            title_val = asset_ref_titles[i]

            attempt = 0
            while attempt < 20:
                if tier == 1:
                    template = self.safe_choice(tier1_templates)
                elif tier == 2:
                    template = self.safe_choice(tier2_templates)
                else:
                    template = self.safe_choice(tier3_templates)

                caption = template.format(modality=modality_val, title=title_val)
                # Add uniqueness suffix if needed
                if caption not in used_captions:
                    used_captions.add(caption)
                    visual_captions.append(caption)
                    break
                attempt += 1
            else:
                # Fallback unique caption
                unique_suffix = f" [Record {i}]"
                fallback = (
                    f"This {modality_val} asset presents visual content referenced as '{title_val}', "
                    f"captured for brand asset discovery and multimodal search indexing purposes. "
                    f"The asset supports marketing technology workflows across digital channels.{unique_suffix}"
                )
                used_captions.add(fallback)
                visual_captions.append(fallback)

        return pd.DataFrame({
            "embedding_id": embedding_ids,
            "asset_ref_title": asset_ref_titles,
            "visual_caption": visual_captions,
            "source_asset_id": source_asset_ids,
            "embedding_model_version": embedding_model_versions,
            "modality": modalities,
            "owner_account_id": owner_account_ids,
            "capture_date": capture_dates,
        })

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships from requirements"""
        return [
            # visual_asset_embeddings: brand_asset_catalog
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {
            'brand_asset_catalog': 'Brand Asset Catalog (documents)',
            'template_library': 'Template Library (documents)',
            'visual_asset_embeddings': 'Visual Asset Embeddings (documents)',
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Return fields that should use semantic_text mapping"""
        return {
            'brand_asset_catalog': ['asset_description'],
            'template_library': ['template_description'],
            'visual_asset_embeddings': ['visual_caption'],
        }
