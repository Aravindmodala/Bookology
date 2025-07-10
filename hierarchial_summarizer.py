"""
Hierarchical Summarization Module for Bookology

This module implements hierarchical summarization + sliding window approach
to reduce token usage while maintaining story continuity for long Stories.

Key Features:
- Generates super-summaries every N Chapters (e.g., every 5 Chapters)
- Uses sliding window for recent Chapters (e.g., last 3 Chapters)
- Smart context truncation to fit within token limits
- Maintains story continuity while reducing input tokens

How it works:
1. For Chapter 1-5: Just use individual chapter summaries
2. For Chapter 6: Use super-summary of Chapters 1-5 + recent summaries
3. For Chapter 10: Use super-summary of Chapters 1-5 + super-summary of 6-10 + recent summaries
"""

from typing import List, Dict, Optional, Tuple
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HierarchicalSummarizer:
    """
    Manages hierarchical summarization for long Stories.
    
    This class reduces token usage while maintaining story continuity by:
    - Creating super-summaries every N Chapters
    - Using sliding window for recent Chapters
    - Smart truncation to fit within token limits
    """
    
    def __init__(self, super_summary_interval: int = 5, sliding_window_size: int = 3):
        """
        Initialize the hierarchical summarizer.
        
        Args:
            super_summary_interval: Generate super-summary every N Chapters (default: 5)
            sliding_window_size: Number of recent chapter summaries to include (default: 3)
        """
        self.super_summary_interval = super_summary_interval
        self.sliding_window_size = sliding_window_size
        
        logger.info(f"🏗️ Initializing HierarchicalSummarizer:")
        logger.info(f"   📊 Super-summary interval: every {super_summary_interval} Chapters")
        logger.info(f"   🪟 Sliding window size: {sliding_window_size} recent Chapters")
        
        # Initialize LLM for super-summary generation (using ChatOpenAI for GPT-4o-mini)
        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.3,  # Lower temperature for consistent summaries
            max_tokens=800,   # Moderate length for super-summaries
            model_name="gpt-4o-mini"
        )
        
        logger.info(f"🤖 LLM initialized: {self.llm.model_name} (temp={self.llm.temperature})")
        
        # Prompt for generating super-summaries
        self.super_summary_prompt = PromptTemplate(
            input_variables=["chapter_summaries", "start_chapter", "end_chapter"],
            template="""You are a master storyteller creating a concise super-summary of multiple Chapters.

CHAPTER SUMMARIES TO COMBINE:
{chapter_summaries}

Create a single, coherent super-summary covering Chapters {start_chapter} through {end_chapter} that:
• Captures the main plot developments and character arcs
• Maintains story flow and continuity
• Is concise but comprehensive (3-4 sentences maximum)
• Focuses on what's most important for future Chapters
• Preserves key character relationships and plot points

SUPER-SUMMARY:"""
        )
        
        # Build the super-summary chain (using new syntax compatible with ChatOpenAI)
        self.super_summary_chain = self.super_summary_prompt | self.llm
        
        logger.info("✅ HierarchicalSummarizer initialized successfully")
    
    def should_generate_super_summary(self, chapter_number: int) -> bool:
        """
        Check if we should generate a super-summary for this chapter number.
        
        Args:
            chapter_number: The current chapter number
            
        Returns:
            True if a super-summary should be generated
        """
        return chapter_number % self.super_summary_interval == 0
    
    def get_super_summary_range(self, chapter_number: int) -> Tuple[int, int]:
        """
        Get the chapter range for the super-summary that includes this chapter.
        
        Args:
            chapter_number: The current chapter number
            
        Returns:
            Tuple of (start_chapter, end_chapter) for the super-summary
        """
        start_chapter = ((chapter_number - 1) // self.super_summary_interval) * self.super_summary_interval + 1
        end_chapter = min(start_chapter + self.super_summary_interval - 1, chapter_number)
        return start_chapter, end_chapter
    
    def generate_super_summary(self, chapter_summaries: List[str], start_chapter: int, end_chapter: int) -> str:
        """
        Generate a super-summary from multiple chapter summaries.
        
        Args:
            chapter_summaries: List of chapter summaries to combine
            start_chapter: Starting chapter number
            end_chapter: Ending chapter number
            
        Returns:
            Generated super-summary text
        """
        try:
            logger.info(f"🔄 Generating super-summary for Chapters {start_chapter}-{end_chapter}")
            logger.info(f"📊 Combining {len(chapter_summaries)} chapter summaries")
            
            # Format chapter summaries for the prompt
            formatted_summaries = ""
            for i, summary in enumerate(chapter_summaries, start_chapter):
                # Truncate individual summaries if they're too long
                truncated_summary = summary.strip()
                if len(truncated_summary) > 400:  # Limit individual summaries
                    truncated_summary = truncated_summary[:400] + "..."
                formatted_summaries += f"Chapter {i}: {truncated_summary}\n"
            
            logger.info(f"📝 Input to super-summary LLM: {len(formatted_summaries)} chars")
            
            # Generate super-summary using LLM
            result = self.super_summary_chain.invoke({
                "chapter_summaries": formatted_summaries,
                "start_chapter": start_chapter,
                "end_chapter": end_chapter
            })
            
            super_summary = result.content.strip()
            
            # Log results
            logger.info(f"✅ Super-summary generated successfully")
            logger.info(f"📏 Super-summary length: {len(super_summary)} chars")
            logger.info(f"📝 Super-summary preview: {super_summary[:150]}...")
            
            return super_summary
            
        except Exception as e:
            logger.error(f"❌ Error generating super-summary: {e}")
            # Fallback: combine summaries with simple concatenation
            fallback_summary = f"Chapters {start_chapter}-{end_chapter}: {' '.join(chapter_summaries[:2])}..."
            logger.warning(f"🔄 Using fallback super-summary: {fallback_summary[:100]}...")
            return fallback_summary
    
    def get_context_for_chapter(self, 
                               chapter_number: int, 
                               all_chapter_summaries: Dict[int, str],
                               story_outline: str) -> Dict[str, str]:
        """
        Get the optimal context for generating a specific chapter.
        
        This is the main method that combines:
        - Story outline (possibly truncated)
        - Super-summaries from previous chapter groups
        - Recent chapter summaries (sliding window)
        
        Args:
            chapter_number: The chapter number to generate
            all_chapter_summaries: Dict mapping chapter numbers to their summaries
            story_outline: The original story outline
            
        Returns:
            Dict with keys: 'story_outline', 'super_summary', 'recent_summaries'
        """
        logger.info(f"📚 Building context for Chapter {chapter_number}")
        logger.info(f"📊 Available chapter summaries: {list(all_chapter_summaries.keys())}")
        
        context = {
            'story_outline': story_outline,
            'super_summary': '',
            'recent_summaries': ''
        }
        
        # 1. Generate super-summary if we have enough Chapters
        if chapter_number > self.super_summary_interval:
            # Find the most recent complete super-summary range
            super_summary_end = ((chapter_number - 1) // self.super_summary_interval) * self.super_summary_interval
            start_chapter, end_chapter = self.get_super_summary_range(super_summary_end)
            
            logger.info(f"🔍 Checking for super-summary range: Chapters {start_chapter}-{end_chapter}")
            
            # Check if we have all the chapter summaries needed for this super-summary
            required_Chapters = list(range(start_chapter, end_chapter + 1))
            missing_Chapters = [ch for ch in required_Chapters if ch not in all_chapter_summaries]
            
            if not missing_Chapters:
                # We have all summaries needed for the super-summary
                chapter_summaries_for_super = [all_chapter_summaries[ch] for ch in required_Chapters]
                context['super_summary'] = self.generate_super_summary(
                    chapter_summaries_for_super, start_chapter, end_chapter
                )
                logger.info(f"📖 Generated super-summary for Chapters {start_chapter}-{end_chapter}")
            else:
                logger.warning(f"⚠️ Missing summaries for Chapters: {missing_Chapters}, skipping super-summary")
        
        # 2. Get recent chapter summaries (sliding window)
        # Start from after the super-summary range (if exists) or from the beginning
        recent_start = max(1, chapter_number - self.sliding_window_size)
        if context['super_summary']:  # If we have a super-summary, start after it
            super_summary_end = ((chapter_number - 1) // self.super_summary_interval) * self.super_summary_interval
            recent_start = max(recent_start, super_summary_end + 1)
        
        recent_Chapters = []
        for i in range(recent_start, chapter_number):
            if i in all_chapter_summaries:
                chapter_summary = all_chapter_summaries[i].strip()
                # Truncate long summaries
                if len(chapter_summary) > 300:
                    chapter_summary = chapter_summary[:300] + "..."
                recent_Chapters.append(f"Chapter {i}: {chapter_summary}")
        
        if recent_Chapters:
            context['recent_summaries'] = '\n'.join(recent_Chapters)
            logger.info(f"📄 Using {len(recent_Chapters)} recent chapter summaries (Chapters {recent_start}-{chapter_number-1})")
        else:
            logger.info("📄 No recent chapter summaries available")
        
        # 3. Log context summary
        total_context_chars = (
            len(context['story_outline']) + 
            len(context['super_summary']) + 
            len(context['recent_summaries'])
        )
        estimated_tokens = total_context_chars // 4  # Rough estimate
        
        logger.info(f"📊 Context summary for Chapter {chapter_number}:")
        logger.info(f"   📋 Story outline: {len(context['story_outline'])} chars")
        logger.info(f"   📖 Super-summary: {len(context['super_summary'])} chars")
        logger.info(f"   📄 Recent summaries: {len(context['recent_summaries'])} chars")
        logger.info(f"   📏 Total context: {total_context_chars} chars (~{estimated_tokens} tokens)")
        
        return context
    
    def truncate_context(self, context: Dict[str, str], max_chars: int = 8000) -> Dict[str, str]:
        """
        Truncate context if it's too long to fit within token limits.
        
        Prioritization order (most important first):
        1. recent_summaries (immediate continuity)
        2. super_summary (broader context)
        3. story_outline (background context)
        
        Args:
            context: Context dictionary to truncate
            max_chars: Maximum total characters allowed (~2000 tokens)
            
        Returns:
            Truncated context dictionary
        """
        total_chars = sum(len(v) for v in context.values())
        
        if total_chars <= max_chars:
            logger.info(f"✅ Context within limits: {total_chars}/{max_chars} chars")
            return context
        
        logger.warning(f"⚠️ Context too long ({total_chars} chars), truncating to {max_chars}")
        
        truncated_context = context.copy()
        
        # Priority 1: Preserve recent summaries (most important for continuity)
        max_recent = max_chars // 2  # Allocate 50% to recent summaries
        if len(truncated_context['recent_summaries']) > max_recent:
            truncated_context['recent_summaries'] = truncated_context['recent_summaries'][:max_recent] + "...[truncated]"
            logger.info(f"📄 Truncated recent summaries to {len(truncated_context['recent_summaries'])} chars")
        
        # Priority 2: Truncate super-summary if needed
        remaining_chars = max_chars - len(truncated_context['recent_summaries'])
        max_super = remaining_chars // 2  # Allocate half of remaining to super-summary
        if len(truncated_context['super_summary']) > max_super:
            truncated_context['super_summary'] = truncated_context['super_summary'][:max_super] + "...[truncated]"
            logger.info(f"📖 Truncated super-summary to {len(truncated_context['super_summary'])} chars")
        
        # Priority 3: Truncate story outline with whatever remains
        remaining_chars = max_chars - len(truncated_context['recent_summaries']) - len(truncated_context['super_summary'])
        if len(truncated_context['story_outline']) > remaining_chars:
            truncated_context['story_outline'] = truncated_context['story_outline'][:remaining_chars] + "...[truncated]"
            logger.info(f"📋 Truncated story outline to {len(truncated_context['story_outline'])} chars")
        
        final_chars = sum(len(v) for v in truncated_context.values())
        final_tokens = final_chars // 4
        logger.info(f"✅ Context truncated to {final_chars} characters (~{final_tokens} tokens)")
        
        return truncated_context
    
    def format_context_for_llm(self, context: Dict[str, str]) -> str:
        """
        Format the context into a single string suitable for LLM input.
        
        Args:
            context: Context dictionary from get_context_for_chapter()
            
        Returns:
            Formatted context string
        """
        formatted_parts = []
        
        # Add story outline
        if context['story_outline']:
            formatted_parts.append(f"STORY OUTLINE:\n{context['story_outline']}")
        
        # Add super-summary if available
        if context['super_summary']:
            formatted_parts.append(f"PREVIOUS Chapters SUMMARY:\n{context['super_summary']}")
        
        # Add recent summaries
        if context['recent_summaries']:
            formatted_parts.append(f"RECENT Chapters:\n{context['recent_summaries']}")
        
        formatted_context = "\n\n".join(formatted_parts)
        
        logger.info(f"📝 Formatted context for LLM: {len(formatted_context)} chars")
        return formatted_context


# Create global instance for easy import and use
hierarchical_summarizer = HierarchicalSummarizer()

# Helper function for easy access
def get_smart_context_for_chapter(
    chapter_number: int,
    all_chapter_summaries: Dict[int, str],
    story_outline: str,
    max_chars: int = 8000
) -> str:
    """
    Convenience function to get smart, token-optimized context for chapter generation.
    
    Args:
        chapter_number: The chapter number to generate
        all_chapter_summaries: Dict mapping chapter numbers to their summaries
        story_outline: The original story outline
        max_chars: Maximum characters allowed in context
        
    Returns:
        Formatted context string ready for LLM input
    """
    # Get context using hierarchical summarization
    context = hierarchical_summarizer.get_context_for_chapter(
        chapter_number, all_chapter_summaries, story_outline
    )
    
    # Truncate if necessary
    truncated_context = hierarchical_summarizer.truncate_context(context, max_chars)
    
    # Format for LLM
    formatted_context = hierarchical_summarizer.format_context_for_llm(truncated_context)
    
    return formatted_context
