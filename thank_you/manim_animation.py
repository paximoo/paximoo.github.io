from manim import *

class FarewellAni(Scene):
    def construct(self):
        #Content
        CSText = Text("Computer Science...", font_size = 48)
        HardText = Text("A Subject known for it's Tough and Logical Nature", font_size = 40)
        YetText = Text("And Yet, Here we all are...\n\nAble to Understand and Use\n2 years worth of CS content", font_size = 40, color = LIGHT_PINK)
        ThanksText = Text("All Thanks to...")
        MaamText = Text("Ms. Payal Maheshwari", font_size = 38)
        HeartText = Text("From the Bottom of all of our Hearts", color = ORANGE)
        MaamText2 = Text("Thanks a ton Ma'am for:")
        ListText = Text('''
• Teaching us Computer Science
• Managing our Shenanigans in class
• Being a Trusted Adult we could talk openly to
• Being a Constant Presence in our Regular School Days
                        
And Much Much more....''', font_size = 38, line_spacing = 1)
        ByeText = Text("But,\nI guess all good things must come to an End...\n\nAnd Now it's Time for us to go")
        ByeText2 = Text("We will forever remember you as our\nFavourite Teacher :D", font_size = 38)
        ByeText2.set_color_by_gradient(YELLOW, TEAL)
        HealText = Text("Oh and also,\nGet well soon Ma'am from your Injuries\n\nThe next Batch eagerly awaits you ❤️", color = BLUE_B)
        FinalText = Text("Once again,\nThankYou for Everything Ma'am! :)", font_size = 40, color = YELLOW)
        CredText = Text("Crafted (with Love) by:\n\nBatch of CS 2024-2026")
        CredText.set_color_by_gradient(BLUE, PINK)

        #Animation Player
        self.play(Write(CSText), run_time = 1, rate_func = smooth)
        self.wait(1)
        self.play(
            CSText.animate
                .shift(UP * 1.2)
                .set_color(ORANGE),
            run_time = 2.5,
            rate_func = smooth
        )
        self.play(Write(HardText), run_time = 1.5, rate_func = smooth)
        self.wait(2.4)
        self.play(FadeOut(CSText))
        self.wait(1)
        self.play(Unwrite(HardText))
        self.wait(1)
        self.play(Write(YetText), run_time = 3, rate_func = smooth)
        self.wait(2.6)
        self.play(FadeOut(YetText))
        self.wait(1)
        self.play(Write(ThanksText))
        self.wait(1.5)
        self.play(Unwrite(ThanksText))
        self.wait(0.5)
        star = Star(
            n=5,
            outer_radius = 3.6,
            inner_radius = 1.6,
            color = BLUE
        )
        MaamText.move_to(star.get_center() + UP * 0.4)
        self.play(Create(star), run_time = 3)
        self.play(FadeIn(MaamText), run_time = 1, rate_func = smooth)
        self.wait(2)
        self.play(Uncreate(star), run_time = 2)
        self.wait(0.4)
        self.play(FadeOut(MaamText))
        self.wait(0.5)
        self.play(Write(HeartText), run_time = 1, rate_func = smooth)
        self.wait(1.5)
        self.play(FadeOut(HeartText), run_time = 1)
        self.wait(0.5)
        self.play(Write(MaamText2), run_time = 1, rate_func = smooth)
        self.wait(1)
        self.play(
                    MaamText2.animate
                        .shift(UP * 2.8)
                        .set_color(YELLOW),
                    run_time = 2,
                    rate_func = smooth
                )
        self.play(Write(ListText), run_time = 6, rate_func=smooth)
        self.wait(5)
        self.play(FadeOut(MaamText2), run_time = 1, rate_func = smooth)
        self.wait(1)
        self.play(Unwrite(ListText), run_time = 3, rate_func=smooth)
        self.wait(1)
        self.play(FadeIn(ByeText), run_time = 2, rate_func = smooth)
        self.wait(1)
        self.play(
                    ByeText.animate.set_color(RED),
                    run_time = 2,
                    rate_func = smooth
                )
        self.wait(2)
        self.play(ShrinkToCenter(ByeText), run_time = 2, rate_func = smooth)
        self.wait(0.5)
        self.play(Write(ByeText2), run_time = 2, rate_func = smooth)
        self.wait(2)
        self.play(FadeOut(ByeText2))
        self.wait(1)
        self.play(FadeIn(HealText), run_time = 2, rate_func = smooth)
        self.wait(4)
        self.play(Unwrite(HealText), run_time = 1, rate_func = smooth)
        self.wait(0.4)
        self.play(FadeIn(FinalText), run_time = 3, rate_func = smooth)
        self.wait(2)
        self.play(FadeOut(FinalText), run_time = 1, rate_func = smooth)
        self.wait(1)
        self.play(Write(CredText), run_time = 2, rate_func = smooth)
        self.wait(2)
        self.play(ShrinkToCenter(CredText), run_time = 1.6, rate_func = smooth)