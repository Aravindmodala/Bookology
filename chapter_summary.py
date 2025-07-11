import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import logging

# Setup logging
from logger_config import setup_summary_logger
logger = setup_summary_logger()

# Load environment variables
load_dotenv()

# Initialize the LLM for summary generation (using ChatOpenAI for GPT-4o-mini)
summary_llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), 
    model_name='gpt-4o-mini', 
    temperature=0.3,  # Lower temperature for more consistent summaries
    max_tokens=500    # Summaries should be concise
)

# Create a prompt template for chapter summarization
summary_prompt = PromptTemplate(
    input_variables=["chapter_content", "chapter_number", "story_context"],
    template="""You are a professional story editor who creates concise, accurate chapter summaries for story continuity.

Your task is to create a summary of Chapter {chapter_number} that will help maintain story continuity for future Chapters.

STORY CONTEXT:
{story_context}

CHAPTER {chapter_number} CONTENT:
{chapter_content}

Create a concise summary (5-8 sentences) that includes:
- Key events that happened in this chapter
- Important character developments or introductions
- Critical plot points or revelations
- Setting/location changes
- Any cliffhangers or hooks for the next chapter

Focus on information that will be important for generating future Chapters. Be specific but concise.

SUMMARY:"""
)

# Build the chain
summary_chain = summary_prompt | summary_llm

def generate_chapter_summary(
    chapter_content: str, 
    chapter_number: int = 1,
    story_context: str = "",
    story_title: str = "Untitled Story"
) -> Dict[str, Any]:
    """
    Generate a summary of a chapter using LLM.
    
    Args:
        chapter_content: The full text of the chapter to summarize
        chapter_number: The chapter number being summarized
        story_context: Context about the story (outline, previous summaries, etc.)
        story_title: Title of the story for context
    
    Returns:
        Dict containing the summary and metadata
    """
    try:
        logger.info(f"🤖 SUMMARY LLM: Starting summary generation for Chapter {chapter_number} of '{story_title}'...")
        
        # Log input parameters
        logger.info(f"📊 SUMMARY LLM: Input parameters:")
        logger.info(f"   📝 Chapter content length: {len(chapter_content)} chars")
        logger.info(f"   📄 Story context length: {len(story_context)} chars")
        logger.info(f"   📖 Story title: '{story_title}'")
        logger.info(f"   📑 Chapter number: {chapter_number}")
        
        # Capture LLM parameters for metrics
        llm_temperature = summary_llm.temperature
        llm_model = summary_llm.model_name
        llm_max_tokens = summary_llm.max_tokens
        
        logger.info(f"⚙️ SUMMARY LLM: Model configuration:")
        logger.info(f"   🤖 Model: {llm_model}")
        logger.info(f"   🌡️ Temperature: {llm_temperature}")
        logger.info(f"   🎯 Max tokens: {llm_max_tokens}")
        
        # Calculate input metrics
        input_word_count = len(chapter_content.split())
        context_word_count = len(story_context.split())
        total_input_words = input_word_count + context_word_count
        
        logger.info(f"📊 SUMMARY LLM: Input metrics:")
        logger.info(f"   📝 Chapter words: {input_word_count}")
        logger.info(f"   📄 Context words: {context_word_count}")
        logger.info(f"   📋 Total input words: {total_input_words}")
        
        # Log what we're sending to the LLM
        logger.info(f"🎯 SUMMARY LLM: Preparing LLM prompt...")
        logger.info(f"📄 SUMMARY LLM: Story context preview: {story_context[:200]}...")
        logger.info(f"📝 SUMMARY LLM: Chapter content preview: {chapter_content[:200]}...")
        
        # Generate the summary
        logger.info(f"🚀 SUMMARY LLM: Calling LLM chain...")
        
        try:
            result = summary_chain.invoke({
                "chapter_content": chapter_content,
                "chapter_number": chapter_number,
                "story_context": story_context
            })
            
            logger.info(f"✅ SUMMARY LLM: LLM chain completed successfully")
            logger.info(f"📊 SUMMARY LLM: Raw result type: {type(result)}")
            logger.info(f"📝 SUMMARY LLM: Raw result length: {len(str(result))} chars")
            
        except Exception as llm_error:
            logger.error(f"❌ SUMMARY LLM: LLM chain failed: {str(llm_error)}")
            logger.error(f"🔍 SUMMARY LLM: Error type: {type(llm_error)}")
            raise llm_error
        
        summary_text = result.content.strip()
        
        logger.info(f"🔧 SUMMARY LLM: Processing LLM response...")
        logger.info(f"📝 SUMMARY LLM: Summary text after strip: {len(summary_text)} chars")
        
        # Calculate output metrics
        output_word_count = len(summary_text.split())
        
        # Estimate token usage
        estimated_input_tokens = int(total_input_words * 1.33)
        estimated_output_tokens = int(output_word_count * 1.33)
        estimated_total_tokens = estimated_input_tokens + estimated_output_tokens
        
        logger.info(f"📊 SUMMARY LLM: Output metrics calculated:")
        logger.info(f"   📝 Summary words: {output_word_count}")
        logger.info(f"   📏 Summary length: {len(summary_text)} characters")
        logger.info(f"   🎯 Estimated input tokens: {estimated_input_tokens}")
        logger.info(f"   🎯 Estimated output tokens: {estimated_output_tokens}")
        logger.info(f"   🎯 Estimated total tokens: {estimated_total_tokens}")
        
        # Show compression ratio
        compression_ratio = round(output_word_count / max(input_word_count, 1), 3)
        logger.info(f"📉 SUMMARY LLM: Compression ratio: {compression_ratio} ({output_word_count}/{input_word_count})")
        
        # Log the actual summary generated
        logger.info(f"✅ SUMMARY LLM: Summary generated successfully!")
        logger.info(f"📝 SUMMARY LLM: Full summary preview: {summary_text[:200]}...")
        
        final_result = {
            "success": True,
            "summary": summary_text,
            "metadata": {
                "chapter_number": chapter_number,
                "story_title": story_title,
                "original_word_count": input_word_count,
                "summary_word_count": output_word_count,
                "compression_ratio": compression_ratio,
                "summary_length": len(summary_text)
            },
            "usage_metrics": {
                "temperature_used": llm_temperature,
                "model_used": llm_model,
                "max_tokens": llm_max_tokens,
                "input_word_count": total_input_words,
                "output_word_count": output_word_count,
                "estimated_input_tokens": estimated_input_tokens,
                "estimated_output_tokens": estimated_output_tokens,
                "estimated_total_tokens": estimated_total_tokens
            }
        }
        
        logger.info(f"🎉 SUMMARY LLM: Returning successful result")
        logger.info(f"📋 SUMMARY LLM: Result keys: {list(final_result.keys())}")
        
        return final_result
        
    except Exception as e:
        logger.error(f"❌ SUMMARY LLM: FATAL ERROR generating summary for Chapter {chapter_number}: {str(e)}")
        logger.error(f"🔍 SUMMARY LLM: Error type: {type(e)}")
        logger.error(f"🔍 SUMMARY LLM: Error details: {e}")
        
        error_result = {
            "success": False,
            "error": str(e),
            "summary": "",
            "metadata": {
                "chapter_number": chapter_number,
                "story_title": story_title,
                "error": str(e)
            },
            "usage_metrics": {
                "temperature_used": summary_llm.temperature,
                "model_used": summary_llm.model_name,
                "error": str(e)
            }
        }
        
        logger.error(f"❌ SUMMARY LLM: Returning error result")
        return error_result

def build_story_context_for_next_chapter(
    story_outline: str = "",
    previous_chapter_summaries: list = None,
    current_chapter_number: int = 2
) -> str:
    """
    Build context string for generating the next chapter.
    
    Args:
        story_outline: The original story outline
        previous_chapter_summaries: List of summaries from previous Chapters
        current_chapter_number: The chapter number being generated
    
    Returns:
        Formatted context string to include in next chapter generation
    """
    if previous_chapter_summaries is None:
        previous_chapter_summaries = []
    
    context = f"STORY CONTEXT FOR CHAPTER {current_chapter_number}:\n\n"
    
    if story_outline:
        context += f"ORIGINAL STORY OUTLINE:\n{story_outline}\n\n"
    
    if previous_chapter_summaries:
        context += "STORY SO FAR:\n"
        for i, summary in enumerate(previous_chapter_summaries, 1):
            context += f"Chapter {i} Summary: {summary}\n\n"
    
    context += f"Now continue the story with Chapter {current_chapter_number}, maintaining consistency with the above context."
    
    return context

def test_chapter_summary():
    """Test function for the chapter summary generation."""
    test_chapter = """
    Sarah walked through the misty forest, her heart pounding as she heard strange sounds echoing through the trees. 
    The ancient map in her hands seemed to glow faintly in the moonlight, pointing toward a hidden temple that had been 
    lost for centuries. As she approached a clearing, she saw massive stone pillars covered in glowing runes. 
    Suddenly, a figure emerged from behind one of the pillars - it was her missing brother Tom, but something was 
    different about him. His eyes glowed with the same eerie light as the runes, and when he spoke, his voice 
    sounded hollow and distant. "Sarah," he said, "you shouldn't have come here. The temple... it changes people."
    """
    
    result = generate_chapter_summary(
        chapter_content=test_chapter,
        chapter_number=1,
        story_context="A fantasy adventure about siblings searching for an ancient temple",
        story_title="The Lost Temple"
    )
    
    print("=" * 60)
    print("CHAPTER SUMMARY TEST")
    print("=" * 60)
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Summary: {result['summary']}")
        print(f"Compression ratio: {result['metadata']['compression_ratio']}")
        print(f"Model used: {result['usage_metrics']['model_used']}")
        print(f"Estimated tokens: {result['usage_metrics']['estimated_total_tokens']}")
    else:
        print(f"Error: {result['error']}")
    print("=" * 60)

if __name__ == "__main__":
    # Run test when script is executed directly
    test_chapter_summary()
