import io
import os
from typing import Dict, Any, List, Optional
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

from app.models.schemas import SlideDeck, Slide


class PPTXBuilder:
    """Production PowerPoint generator rendering modern, beautiful 16:9 presentations."""

    THEMES: Dict[str, Dict[str, RGBColor]] = {
        "modern_indigo": {
            "bg": RGBColor(11, 15, 25),          # #0B0F19 Deep Obsidian
            "card_bg": RGBColor(26, 34, 52),     # #1A2234 Dark Slate Card
            "card_border": RGBColor(51, 65, 85), # #334155
            "accent_primary": RGBColor(99, 102, 241), # #6366F1 Electric Indigo
            "accent_secondary": RGBColor(56, 189, 248), # #38BDF8 Sky Cyan
            "title_text": RGBColor(255, 255, 255),
            "takeaway_text": RGBColor(224, 231, 255),
            "body_text": RGBColor(203, 213, 225),
            "muted_text": RGBColor(148, 163, 184),
            "tag_bg": RGBColor(49, 46, 129),
            "tag_text": RGBColor(199, 210, 254)
        },
        "executive_navy": {
            "bg": RGBColor(10, 25, 47),          # #0A192F Boardroom Navy
            "card_bg": RGBColor(20, 38, 71),     # #142647 Card
            "card_border": RGBColor(35, 62, 102),
            "accent_primary": RGBColor(245, 158, 11), # #F59E0B Warm Amber Gold
            "accent_secondary": RGBColor(45, 212, 191), # Teal
            "title_text": RGBColor(248, 250, 252),
            "takeaway_text": RGBColor(254, 243, 199),
            "body_text": RGBColor(226, 232, 240),
            "muted_text": RGBColor(148, 163, 184),
            "tag_bg": RGBColor(120, 53, 15),
            "tag_text": RGBColor(253, 230, 138)
        },
        "emerald_clean": {
            "bg": RGBColor(6, 44, 34),           # #062C22 Deep Emerald
            "card_bg": RGBColor(14, 64, 50),     # Forest Card
            "card_border": RGBColor(24, 94, 75),
            "accent_primary": RGBColor(16, 185, 129), # #10B981 Vivid Mint
            "accent_secondary": RGBColor(110, 231, 183),
            "title_text": RGBColor(255, 255, 255),
            "takeaway_text": RGBColor(209, 250, 229),
            "body_text": RGBColor(226, 232, 240),
            "muted_text": RGBColor(156, 163, 175),
            "tag_bg": RGBColor(6, 78, 59),
            "tag_text": RGBColor(167, 243, 208)
        },
        "nordic_light": {
            "bg": RGBColor(248, 250, 252),       # #F8FAFC Clean Light
            "card_bg": RGBColor(255, 255, 255),  # Pure White Card
            "card_border": RGBColor(226, 232, 240),
            "accent_primary": RGBColor(37, 99, 235), # #2563EB Royal Blue
            "accent_secondary": RGBColor(14, 165, 233),
            "title_text": RGBColor(15, 23, 42),
            "takeaway_text": RGBColor(30, 58, 138),
            "body_text": RGBColor(51, 65, 85),
            "muted_text": RGBColor(100, 116, 139),
            "tag_bg": RGBColor(219, 234, 254),
            "tag_text": RGBColor(29, 78, 216)
        }
    }

    def build_presentation(self, deck: SlideDeck, theme_name: str = "modern_indigo") -> io.BytesIO:
        """Constructs and returns the PowerPoint presentation binary stream."""
        prs = Presentation()
        # Set 16:9 Widescreen aspect ratio
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        # Select layout (blank slide)
        blank_layout = prs.slide_layouts[6]
        palette = self.THEMES.get(theme_name, self.THEMES["modern_indigo"])

        for slide_data in deck.slides:
            slide = prs.slides.add_slide(blank_layout)
            self._apply_slide_background(slide, palette)

            # Route layout style
            layout_type = slide_data.visual_layout_suggestion.lower()
            if slide_data.slide_number == 1 or "hero" in layout_type or "title" in layout_type:
                self._render_title_hero_layout(slide, slide_data, deck, palette)
            elif "split" in layout_type or "2_column" in layout_type:
                self._render_split_layout(slide, slide_data, palette)
            elif "3_pillar" in layout_type or "cards" in layout_type:
                self._render_three_pillar_layout(slide, slide_data, palette)
            elif "kpi" in layout_type or "metric" in layout_type:
                self._render_kpi_layout(slide, slide_data, palette)
            elif "timeline" in layout_type or "flow" in layout_type or "roadmap" in layout_type:
                self._render_timeline_layout(slide, slide_data, palette)
            else:
                self._render_bullet_list_layout(slide, slide_data, palette)

            # Attach speaker notes
            if slide_data.speaker_notes:
                notes_slide = slide.notes_slide
                text_frame = notes_slide.notes_text_frame
                text_frame.text = slide_data.speaker_notes

            # Attach citations footer
            self._render_footer(slide, slide_data, palette)

        output_stream = io.BytesIO()
        prs.save(output_stream)
        output_stream.seek(0)
        return output_stream

    def _apply_slide_background(self, slide, palette: Dict[str, RGBColor]):
        """Sets consistent background canvas color."""
        bg_shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0), Inches(0), Inches(13.333), Inches(7.5)
        )
        bg_shape.fill.solid()
        bg_shape.fill.fore_color.rgb = palette["bg"]
        bg_shape.line.color.rgb = palette["bg"]

    def _render_header(self, slide, slide_data: Slide, palette: Dict[str, RGBColor]):
        """Renders standard top header with category pill, title, and takeaway bar."""
        # Category / Slide Number Pill
        badge_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(3.0), Inches(0.35))
        tf_badge = badge_box.text_frame
        tf_badge.word_wrap = True
        p_badge = tf_badge.paragraphs[0]
        p_badge.text = f"SLIDE {slide_data.slide_number:02d} • {slide_data.visual_layout_suggestion.upper().replace('_', ' ')}"
        p_badge.font.size = Pt(10)
        p_badge.font.bold = True
        p_badge.font.color.rgb = palette["accent_secondary"]

        # Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.9))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = slide_data.title
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = palette["title_text"]

    def _render_title_hero_layout(self, slide, slide_data: Slide, deck: SlideDeck, palette: Dict[str, RGBColor]):
        """High-impact executive title cover slide."""
        # Decorative Accent Bar
        accent_bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(1.0), Inches(1.1), Inches(0.2), Inches(3.8)
        )
        accent_bar.fill.solid()
        accent_bar.fill.fore_color.rgb = palette["accent_primary"]
        accent_bar.line.fill.background()

        # Deck Title & Subtitle Box
        title_box = slide.shapes.add_textbox(Inches(1.4), Inches(1.0), Inches(10.8), Inches(2.2))
        tf = title_box.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = deck.deck_title
        p1.font.size = Pt(36)
        p1.font.bold = True
        p1.font.color.rgb = palette["title_text"]

        p2 = tf.add_paragraph()
        p2.text = f"Prepared for: {deck.target_audience}"
        p2.font.size = Pt(16)
        p2.font.color.rgb = palette["accent_secondary"]
        p2.space_before = Pt(12)

        # Core Takeaway Banner Card
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(1.4), Inches(3.4), Inches(10.8), Inches(1.5)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = palette["card_bg"]
        card.line.color.rgb = palette["card_border"]
        card.line.width = Pt(1.5)

        tf_card = card.text_frame
        tf_card.word_wrap = True
        p_card_label = tf_card.paragraphs[0]
        p_card_label.text = "CORE STRATEGIC MANDATE"
        p_card_label.font.size = Pt(11)
        p_card_label.font.bold = True
        p_card_label.font.color.rgb = palette["accent_primary"]

        p_card_body = tf_card.add_paragraph()
        p_card_body.text = slide_data.core_takeaway
        p_card_body.font.size = Pt(15)
        p_card_body.font.color.rgb = palette["takeaway_text"]
        p_card_body.space_before = Pt(6)

        # Bottom Agenda Key Bullets
        bullet_box = slide.shapes.add_textbox(Inches(1.4), Inches(5.1), Inches(10.8), Inches(1.5))
        tf_b = bullet_box.text_frame
        tf_b.word_wrap = True
        for idx, bullet in enumerate(slide_data.bullet_points[:3]):
            p = tf_b.paragraphs[0] if idx == 0 else tf_b.add_paragraph()
            p.text = f"•  {bullet}"
            p.font.size = Pt(13)
            p.font.color.rgb = palette["body_text"]
            p.space_before = Pt(6)

    def _render_split_layout(self, slide, slide_data: Slide, palette: Dict[str, RGBColor]):
        """2-Column Layout: Left Core Takeaway Card, Right Bullets."""
        self._render_header(slide, slide_data, palette)

        # Left Column Card (Takeaway)
        left_card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(0.8), Inches(1.8), Inches(4.2), Inches(4.7)
        )
        left_card.fill.solid()
        left_card.fill.fore_color.rgb = palette["card_bg"]
        left_card.line.color.rgb = palette["accent_primary"]
        left_card.line.width = Pt(2.0)

        tf_left = left_card.text_frame
        tf_left.word_wrap = True

        p_l_label = tf_left.paragraphs[0]
        p_l_label.text = "KEY TAKEAWAY"
        p_l_label.font.size = Pt(12)
        p_l_label.font.bold = True
        p_l_label.font.color.rgb = palette["accent_secondary"]

        p_l_body = tf_left.add_paragraph()
        p_l_body.text = slide_data.core_takeaway
        p_l_body.font.size = Pt(16)
        p_l_body.font.bold = True
        p_l_body.font.color.rgb = palette["takeaway_text"]
        p_l_body.space_before = Pt(14)

        # Right Column Bullets
        right_box = slide.shapes.add_textbox(Inches(5.4), Inches(1.8), Inches(7.1), Inches(4.7))
        tf_right = right_box.text_frame
        tf_right.word_wrap = True

        for idx, bullet in enumerate(slide_data.bullet_points):
            p = tf_right.paragraphs[0] if idx == 0 else tf_right.add_paragraph()
            p.text = f"▶   {bullet}"
            p.font.size = Pt(14)
            p.font.color.rgb = palette["body_text"]
            p.space_before = Pt(16)

    def _render_three_pillar_layout(self, slide, slide_data: Slide, palette: Dict[str, RGBColor]):
        """Three horizontal cards representing core pillars."""
        self._render_header(slide, slide_data, palette)

        # Core Takeaway top banner
        banner = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(0.8), Inches(1.7), Inches(11.7), Inches(0.8)
        )
        banner.fill.solid()
        banner.fill.fore_color.rgb = palette["card_bg"]
        banner.line.color.rgb = palette["card_border"]

        tf_banner = banner.text_frame
        tf_banner.word_wrap = True
        p_b = tf_banner.paragraphs[0]
        p_b.text = f"CORE TAKEAWAY: {slide_data.core_takeaway}"
        p_b.font.size = Pt(12)
        p_b.font.bold = True
        p_b.font.color.rgb = palette["takeaway_text"]

        # 3 Pillar Cards
        card_width = Inches(3.7)
        card_height = Inches(3.7)
        spacing = Inches(0.3)
        start_x = Inches(0.8)
        y_pos = Inches(2.7)

        bullets = slide_data.bullet_points
        for i in range(3):
            x = start_x + (i * (card_width + spacing))
            pillar_card = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                x, y_pos, card_width, card_height
            )
            pillar_card.fill.solid()
            pillar_card.fill.fore_color.rgb = palette["card_bg"]
            pillar_card.line.color.rgb = palette["accent_primary"] if i == 1 else palette["card_border"]
            pillar_card.line.width = Pt(1.5)

            tf_pillar = pillar_card.text_frame
            tf_pillar.word_wrap = True

            p_h = tf_pillar.paragraphs[0]
            p_h.text = f"PILLAR 0{i + 1}"
            p_h.font.size = Pt(12)
            p_h.font.bold = True
            p_h.font.color.rgb = palette["accent_secondary"]

            b_text = bullets[i] if i < len(bullets) else "Strategic alignment and execution focus."
            p_body = tf_pillar.add_paragraph()
            p_body.text = b_text
            p_body.font.size = Pt(13)
            p_body.font.color.rgb = palette["body_text"]
            p_body.space_before = Pt(12)

    def _render_kpi_layout(self, slide, slide_data: Slide, palette: Dict[str, RGBColor]):
        """KPI & Metrics Highlight Layout."""
        self._render_header(slide, slide_data, palette)

        # Highlight Stat / Hero Box
        hero_card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.8)
        )
        hero_card.fill.solid()
        hero_card.fill.fore_color.rgb = palette["card_bg"]
        hero_card.line.color.rgb = palette["accent_primary"]
        hero_card.line.width = Pt(2.0)

        tf_hero = hero_card.text_frame
        tf_hero.word_wrap = True
        p_h1 = tf_hero.paragraphs[0]
        p_h1.text = "PRIMARY METRIC & STRATEGIC IMPACT"
        p_h1.font.size = Pt(11)
        p_h1.font.bold = True
        p_h1.font.color.rgb = palette["accent_secondary"]

        p_h2 = tf_hero.add_paragraph()
        p_h2.text = slide_data.core_takeaway
        p_h2.font.size = Pt(17)
        p_h2.font.bold = True
        p_h2.font.color.rgb = palette["takeaway_text"]
        p_h2.space_before = Pt(8)

        # Supporting Metrics Split Grid
        card_w = Inches(5.7)
        card_h = Inches(2.7)
        start_y = Inches(3.8)

        # Left Metric Card
        left_c = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(0.8), start_y, card_w, card_h
        )
        left_c.fill.solid()
        left_c.fill.fore_color.rgb = palette["card_bg"]
        left_c.line.color.rgb = palette["card_border"]

        tf_lc = left_c.text_frame
        tf_lc.word_wrap = True
        p_lch = tf_lc.paragraphs[0]
        p_lch.text = "OPERATIONAL DRIVERS"
        p_lch.font.size = Pt(11)
        p_lch.font.bold = True
        p_lch.font.color.rgb = palette["accent_primary"]

        if len(slide_data.bullet_points) > 0:
            p_lb = tf_lc.add_paragraph()
            p_lb.text = f"• {slide_data.bullet_points[0]}"
            p_lb.font.size = Pt(13)
            p_lb.font.color.rgb = palette["body_text"]
            p_lb.space_before = Pt(8)
        if len(slide_data.bullet_points) > 1:
            p_lb2 = tf_lc.add_paragraph()
            p_lb2.text = f"• {slide_data.bullet_points[1]}"
            p_lb2.font.size = Pt(13)
            p_lb2.font.color.rgb = palette["body_text"]
            p_lb2.space_before = Pt(6)

        # Right Metric Card
        right_c = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(6.8), start_y, card_w, card_h
        )
        right_c.fill.solid()
        right_c.fill.fore_color.rgb = palette["card_bg"]
        right_c.line.color.rgb = palette["card_border"]

        tf_rc = right_c.text_frame
        tf_rc.word_wrap = True
        p_rch = tf_rc.paragraphs[0]
        p_rch.text = "VERIFIED OUTCOMES"
        p_rch.font.size = Pt(11)
        p_rch.font.bold = True
        p_rch.font.color.rgb = palette["accent_primary"]

        if len(slide_data.bullet_points) > 2:
            p_rb = tf_rc.add_paragraph()
            p_rb.text = f"• {slide_data.bullet_points[2]}"
            p_rb.font.size = Pt(13)
            p_rb.font.color.rgb = palette["body_text"]
            p_rb.space_before = Pt(8)
        if len(slide_data.bullet_points) > 3:
            p_rb2 = tf_rc.add_paragraph()
            p_rb2.text = f"• {slide_data.bullet_points[3]}"
            p_rb2.font.size = Pt(13)
            p_rb2.font.color.rgb = palette["body_text"]
            p_rb2.space_before = Pt(6)

    def _render_timeline_layout(self, slide, slide_data: Slide, palette: Dict[str, RGBColor]):
        """Phased execution / Roadmap timeline layout."""
        self._render_header(slide, slide_data, palette)

        # Core Takeaway top banner
        banner = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(0.8), Inches(1.7), Inches(11.7), Inches(0.8)
        )
        banner.fill.solid()
        banner.fill.fore_color.rgb = palette["card_bg"]
        banner.line.color.rgb = palette["card_border"]

        tf_banner = banner.text_frame
        tf_banner.word_wrap = True
        p_b = tf_banner.paragraphs[0]
        p_b.text = f"STRATEGIC SEQUENCE: {slide_data.core_takeaway}"
        p_b.font.size = Pt(12)
        p_b.font.bold = True
        p_b.font.color.rgb = palette["takeaway_text"]

        # Step Cards
        num_steps = min(4, max(3, len(slide_data.bullet_points)))
        card_w = Inches(11.7 / num_steps - 0.25)
        card_h = Inches(3.7)
        y = Inches(2.7)

        for i in range(num_steps):
            x = Inches(0.8) + (i * (card_w + Inches(0.25)))
            card = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                x, y, card_w, card_h
            )
            card.fill.solid()
            card.fill.fore_color.rgb = palette["card_bg"]
            card.line.color.rgb = palette["accent_primary"] if i == 0 else palette["card_border"]

            tf = card.text_frame
            tf.word_wrap = True

            p1 = tf.paragraphs[0]
            p1.text = f"PHASE 0{i + 1}"
            p1.font.size = Pt(12)
            p1.font.bold = True
            p1.font.color.rgb = palette["accent_secondary"]

            b_text = slide_data.bullet_points[i] if i < len(slide_data.bullet_points) else "Continuous validation and optimization."
            p2 = tf.add_paragraph()
            p2.text = b_text
            p2.font.size = Pt(12)
            p2.font.color.rgb = palette["body_text"]
            p2.space_before = Pt(10)

    def _render_bullet_list_layout(self, slide, slide_data: Slide, palette: Dict[str, RGBColor]):
        """Classic executive bullet list layout with structured takeaway callout."""
        self._render_header(slide, slide_data, palette)

        # Core Takeaway Box
        takeaway_card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.1)
        )
        takeaway_card.fill.solid()
        takeaway_card.fill.fore_color.rgb = palette["card_bg"]
        takeaway_card.line.color.rgb = palette["accent_primary"]
        takeaway_card.line.width = Pt(1.5)

        tf_tk = takeaway_card.text_frame
        tf_tk.word_wrap = True
        p_tk = tf_tk.paragraphs[0]
        p_tk.text = f"KEY TAKEAWAY: {slide_data.core_takeaway}"
        p_tk.font.size = Pt(14)
        p_tk.font.bold = True
        p_tk.font.color.rgb = palette["takeaway_text"]

        # Main Content Card with Bullets
        content_card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(0.8), Inches(3.1), Inches(11.7), Inches(3.4)
        )
        content_card.fill.solid()
        content_card.fill.fore_color.rgb = palette["card_bg"]
        content_card.line.color.rgb = palette["card_border"]

        tf_c = content_card.text_frame
        tf_c.word_wrap = True

        for idx, bullet in enumerate(slide_data.bullet_points):
            p = tf_c.paragraphs[0] if idx == 0 else tf_c.add_paragraph()
            p.text = f"•   {bullet}"
            p.font.size = Pt(14)
            p.font.color.rgb = palette["body_text"]
            p.space_before = Pt(12)

    def _render_footer(self, slide, slide_data: Slide, palette: Dict[str, RGBColor]):
        """Renders subtle citation footer."""
        sources = ", ".join(slide_data.retrieved_sources) if slide_data.retrieved_sources else "Verified Knowledge Base"
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.8), Inches(11.7), Inches(0.4))
        tf = footer_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"Sources: {sources}"
        p.font.size = Pt(9)
        p.font.italic = True
        p.font.color.rgb = palette["muted_text"]


# Global singleton instance
pptx_builder = PPTXBuilder()

