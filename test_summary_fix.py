#!/usr/bin/env python3
"""
Test script to verify that chapter summary generation works properly
with the increased token limit and improved prompt.
"""

import os
import sys
from chapter_summary import generate_chapter_summary

# Test chapter content (your Chapter 1)
test_chapter_content = """
The sun had barely broken over the horizon, casting a fierce golden glow over the sprawling military base that lay just outside the city of Delhi. The air was thick with the scent of burning diesel and freshly polished boots, the sharp tang mingling with the distant sound of jet engines warming up for a morning flight. Major Aarav Singh stood in front of the mirrored wall of his modest quarters, his uniform crisp and neat, betraying none of the turmoil that roiled within him. Each morning felt like a battle, both against the shadows of the past and the weight of the present.

In the quiet solitude of his room, Aarav allowed himself a brief moment to breathe. He ran a hand through his dark hair, feeling the faint tremors of anxiety that had become his unwanted companion since the attack. It had been a week since the bomb had shattered the air of normalcy, turning vibrant streets into scenes of chaos and despair. The faces of those lost—friends, neighbors, innocent children—haunted him like ghosts that refused to pass. The burden of their memory felt heavier today, as if the morning light was too bright, illuminating all that was lost.

Aarav's gaze drifted to the framed photograph on his desk, capturing a moment from happier times—a group of soldiers, arms around one another, laughter frozen in time. Vikram, his best friend, had been in that picture, his wide smile dancing in the sunlight. To think that Vikram would never again share those moments, never again laugh over a cup of tea after a grueling drill, scraped at Aarav's heart. He clenched his jaw, willing the tears back, reminding himself that grief had no place in a soldier's life.

As he dressed, the crisp fabric of his uniform felt more like armor than clothing. It was a shield he donned not just against the cold but against the emotions threatening to engulf him. The medals on his chest glinted in the morning light, a testament to his service yet a painful reminder of battles won and lost. Today, he would lead his men into a mission steeped in pain but also in purpose; it was time to transform that grief into action, to channel the national fury into something tangible.

He stepped outside, the warmth of the sun hitting his face, a welcome contrast to the chill in his heart. The base was coming alive; soldiers moved with purpose, the sound of boots echoing against concrete, mingling with the distant rumble of engines. It was a rhythm he had known since he first enlisted, a cadence that steadied him, even now. But there was a palpable difference in the air, an unspoken tension that wrapped around the camp as tightly as the barbed wire lining the perimeter. They all felt it—the collective grief, the shared determination to avenge the fallen.

As he headed towards the briefing room, he passed a group of young recruits, their faces a mix of excitement and trepidation. It struck him how quickly they were thrust into this world of turmoil, having barely been trained when the call to arms came. Aarav paused for a moment, his heart aching for them. They were eager to prove themselves, to fight for their country, yet the bitter truth of war was that it stripped away innocence, leaving scars that lingered long after the battles ended.

Stepping into the briefing room, the air felt electric with anticipation. The smell of stale coffee hung heavy, intermingling with the scent of sweat and fear. The general stood at the head of the table, his grim expression setting the tone for what was to come. Aarav took his seat among the other officers, feeling the weight of their gazes on him—a mix of respect and expectation. He straightened his back, ready to absorb whatever the general had to say.

"Gentlemen, and ladies," the general began, his voice steady yet strained. "We are here today to discuss our response to the attack that has shaken our nation. As you know, we have identified the terrorist cell responsible, and intelligence suggests they are planning another strike. We cannot allow them the chance to inflict more pain."

Aarav felt a chill run down his spine at the mention of another attack. The thought of more lives lost, more families torn apart, ignited a fire within him. He had already witnessed too much sorrow in recent days; he could not bear to watch it happen again.

The general continued, outlining their mission: a strike against the terrorists' hideout located in the rugged terrain of Jammu and Kashmir. Maps of the area were spread across the table, tactical strategies discussed in clipped tones. Aarav listened, his heart pounding as he absorbed every detail, every risk. The soldiers around him murmured, a low hum of anxious anticipation filling the room. 

"This will not be an easy mission," the general warned, his gaze piercing. "We will be operating in hostile territory, and the enemy will be prepared. I expect each of you to lead your teams with courage and resolve. We owe it to our fallen comrades to show them that their sacrifice was not in vain."

The words resonated deep within Aarav, echoing the promise he had made to Vikram—to protect their brothers and sisters in arms, to honor their sacrifice with action. But doubt crept in, gnawing at the edges of his resolve. What if he wasn't enough? What if he couldn't bring them all back?

As the briefing concluded, Aarav felt a sudden surge of determination coursing through him. He would not let fear dictate his actions. He owed it to Vikram, to the nation, to every soul lost in the tragedy. He had to channel this pain into strength, this grief into action.

After the meeting, he found himself standing outside, the cool air filling his lungs as he prepared for the battle ahead. Lieutenant Priya Rao approached him, her expression a mixture of concern and resolve. "Aarav," she said softly, breaking through the quiet of his thoughts. "Are you okay? You seem... distant."

He forced a smile, though the corners of his mouth felt heavy. "Just processing what's ahead, Priya. You know how it is. We have to stay focused."

She studied him, her eyes searching for the truth beneath his facade. "You can't carry this alone, you know. We're in this together."

Aarav felt a flicker of gratitude for her unwavering support, yet a part of him recoiled at the thought of revealing his fears. He couldn't show weakness, not now, not with so much at stake. "I'll be fine. Just need to clear my head before we head out."

The silence that lingered between them felt heavier than ever, the weight of unspoken words pulling at the threads of their camaraderie. Aarav glanced away, unwilling to confront the vulnerability she saw so clearly. 

As he turned to walk away, a sudden clamor erupted from the command center, voices rising in urgency. Aarav's heart raced as he instinctively moved towards the sound, adrenaline surging through his veins. He knew something was amiss. As he approached, he caught snippets of frantic dialogue and the unwavering tone of authority.

"...new intel has come in. They have a new target..."

Aarav's stomach knotted as he pushed through the gathered soldiers, fear clawing at him in anticipation of what was to come. The room felt charged, the air thick with uncertainty. The command officer was relaying urgent information, but Aarav's focus narrowed as he caught the last words.

"We need to move now. The threat level has escalated."

Aarav's heart dropped as he exchanged glances with Priya, the gravity of the moment settling heavily between them. They could no longer linger in the realm of preparation; the time for action had arrived, propelling them into a storm of chaos where every decision could mean life or death.

Aarav turned to Priya, their eyes locking in a shared understanding. There was no turning back now. The mission awaited, and along with it, the chance to honor those they had lost.

As they made their way towards the hangar, the weight of the moment hung heavily over them—a mix of fear and resolve intertwining as they prepared to step into the unknown. Aarav took a deep breath, grounding himself, knowing that whatever lay ahead would test not just their skills but their very souls.

But as they approached the helicopter, the roar of its blades filling the air, a single thought echoed in Aarav's mind: they would not go quietly into the night. They would fight back against the darkness, for Vikram, for everyone they had lost, and for the future they wished to reclaim.

As he stepped towards the helicopter, the sudden clarity of purpose surged through Aarav, overshadowing the shadows that had lingered too long. He would lead his team into battle, facing the threat head-on, and in that moment of resolve, he felt a glimmer of hope. 

But just as he reached for the door, a chilling new piece of intel hit him like a thunderbolt. "Aarav!" Priya's urgent voice broke through the cacophony, a warning cry laced with fear. 

He turned, heart pounding, as her face turned pale. "They have hostages—we have to make a plan."

Aarav's mind raced, the weight of the situation crashing down on him. The stakes had escalated beyond his worst fears, and with this realization, he knew their mission had transformed into something darker, more dangerous than he had ever anticipated.

Now, it was not just about taking down the enemy; it was about saving lives. And as he stood on the precipice of chaos, he could only hope that he had the strength to navigate the storm ahead.

This was no longer just a mission—it was a fight for humanity itself. And in his heart, he vowed to give everything he had to protect those who could not protect themselves. 

The helicopter blades whirred above them, a siren call to arms, as Aarav took a deep breath, the air heavy with anticipation and dread. The time had come. 

With one last look at Priya, he felt the storm within him awaken, ready to rise and meet the darkness head-on. The battle was about to begin, and he would not falter.

As the doors of the helicopter opened, an unsettling realization gripped him. The choice laid bare before him: lead his team into a fight that could cost them everything or turn back, leaving the hostages to their fate. Aarav's heart raced as the weight of responsibility pressed down...
"""

def test_summary_generation():
    """Test the summary generation with the fixed token limit."""
    
    print("🧪 Testing Chapter Summary Generation...")
    print("=" * 50)
    
    # Test the summary generation
    result = generate_chapter_summary(
        chapter_content=test_chapter_content,
        chapter_number=1,
        story_context="A military thriller about Major Aarav Singh leading a counter-terrorism mission in India.",
        story_title="The Weight of Command"
    )
    
    print(f"✅ Success: {result['success']}")
    
    if result['success']:
        summary = result['summary']
        analysis = result.get('cot_analysis', '')
        metadata = result.get('metadata', {})
        
        print(f"\n📊 METADATA:")
        print(f"   - Original words: {metadata.get('original_word_count', 0)}")
        print(f"   - Summary words: {metadata.get('summary_word_count', 0)}")
        print(f"   - Compression ratio: {metadata.get('compression_ratio', 0)}%")
        print(f"   - Quality score: {metadata.get('quality_score', 0)}/10")
        
        print(f"\n📝 SUMMARY ({len(summary)} chars):")
        print("-" * 30)
        print(summary)
        print("-" * 30)
        
        print(f"\n🧠 ANALYSIS PREVIEW ({len(analysis)} chars):")
        print("-" * 30)
        print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        print("-" * 30)
        
        # Check if summary is complete (not truncated)
        if summary.endswith("...") or len(summary.split()) < 150:
            print("\n❌ ISSUE: Summary appears to be truncated or too short!")
            return False
        else:
            print("\n✅ SUCCESS: Summary appears complete and comprehensive!")
            return True
    else:
        print(f"\n❌ ERROR: {result.get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    success = test_summary_generation()
    
    if success:
        print("\n🎉 Test completed successfully! The summary generation fix is working.")
    else:
        print("\n💥 Test failed! There may still be issues with summary generation.")
        sys.exit(1) 