from typing import AsyncIterator, Tuple, Callable, List, Union, Dict, Any
from functools import wraps
from .output_types import Actions, SentenceOutput, DisplayText
from ..utils.tts_preprocessor import tts_filter as filter_text
from ..live2d_model import Live2dModel
from ..config_manager import TTSPreprocessorConfig
from ..utils.sentence_divider import SentenceDivider
from ..utils.sentence_divider import SentenceWithTags, TagState
from ..utils.korean_cleaner import KoreanCleaner
from loguru import logger


def sentence_divider(
    faster_first_response: bool = True,
    segment_method: str = "pysbd",
    valid_tags: List[str] = None,
):
    """
    Decorator that transforms token stream into sentences with tags

    Args:
        faster_first_response: bool - Whether to enable faster first response
        segment_method: str - Method for sentence segmentation
        valid_tags: List[str] - List of valid tags to process
    """

    def decorator(
        func: Callable[
            ..., AsyncIterator[Union[str, Dict[str, Any]]]
        ],  # Expects str or dict
    ) -> Callable[
        ..., AsyncIterator[Union[SentenceWithTags, Dict[str, Any]]]
    ]:  # Yields SentenceWithTags or dict
        @wraps(func)
        async def wrapper(
            *args, **kwargs
        ) -> AsyncIterator[Union[SentenceWithTags, Dict[str, Any]]]:
            divider = SentenceDivider(
                faster_first_response=faster_first_response,
                segment_method=segment_method,
                valid_tags=valid_tags or [],
            )
            stream_from_func = func(*args, **kwargs)

            # Process the mixed stream using the updated SentenceDivider
            async for item in divider.process_stream(stream_from_func):
                if isinstance(item, SentenceWithTags):
                    logger.debug(f"sentence_divider yielding sentence: {item}")
                elif isinstance(item, dict):
                    logger.debug(f"sentence_divider yielding dict: {item}")
                yield item  # Yield either SentenceWithTags or dict
            # Flushing is handled within divider.process_stream

        return wrapper

    return decorator


def actions_extractor(live2d_model: Live2dModel):
    """
    Decorator that extracts actions from sentences, passing through dicts.
    """

    def decorator(
        func: Callable[
            ..., AsyncIterator[Union[SentenceWithTags, Dict[str, Any]]]
        ],  # Input type hint
    ) -> Callable[
        ..., AsyncIterator[Union[Tuple[SentenceWithTags, Actions], Dict[str, Any]]]
    ]:  # Output type hint
        @wraps(func)
        async def wrapper(
            *args, **kwargs
        ) -> AsyncIterator[
            Union[Tuple[SentenceWithTags, Actions], Dict[str, Any]]
        ]:  # Yield type hint
            stream = func(*args, **kwargs)
            async for item in stream:
                if isinstance(item, SentenceWithTags):
                    sentence = item
                    actions = Actions()
                    # Only extract emotions for non-tag text
                    if not any(
                        tag.state in [TagState.START, TagState.END]
                        for tag in sentence.tags
                    ):
                        expressions = live2d_model.extract_emotion(sentence.text)
                        if expressions:
                            actions.expressions = expressions
                    yield sentence, actions  # Yield the tuple
                elif isinstance(item, dict):
                    # Pass through dictionaries
                    yield item
                else:
                    logger.warning(
                        f"actions_extractor received unexpected type: {type(item)}"
                    )

        return wrapper

    return decorator


def display_processor():
    """
    Decorator that processes text for display, passing through dicts.
    """

    def decorator(
        func: Callable[
            ..., AsyncIterator[Union[Tuple[SentenceWithTags, Actions], Dict[str, Any]]]
        ],  # Input type hint
    ) -> Callable[
        ...,
        AsyncIterator[
            Union[Tuple[SentenceWithTags, DisplayText, Actions], Dict[str, Any]]
        ],
    ]:  # Output type hint
        @wraps(func)
        async def wrapper(
            *args, **kwargs
        ) -> AsyncIterator[
            Union[Tuple[SentenceWithTags, DisplayText, Actions], Dict[str, Any]]
        ]:  # Yield type hint
            stream = func(*args, **kwargs)

            async for item in stream:
                if (
                    isinstance(item, tuple)
                    and len(item) == 2
                    and isinstance(item[0], SentenceWithTags)
                ):
                    sentence, actions = item
                    text = sentence.text
                    # Handle think tag states
                    for tag in sentence.tags:
                        if tag.name == "think":
                            if tag.state == TagState.START:
                                text = "("
                            elif tag.state == TagState.END:
                                text = ")"

                    display = DisplayText(text=text)  # Simplified DisplayText creation
                    yield sentence, display, actions  # Yield the tuple
                elif isinstance(item, dict):
                    # Pass through dictionaries
                    yield item
                else:
                    logger.warning(
                        f"display_processor received unexpected type: {type(item)}"
                    )

        return wrapper

    return decorator


def tts_filter(
    tts_preprocessor_config: TTSPreprocessorConfig = None,
):
    """
    Decorator that filters text for TTS, passing through dicts.
    Skips TTS for think tag content.
    """

    def decorator(
        func: Callable[
            ...,
            AsyncIterator[
                Union[Tuple[SentenceWithTags, DisplayText, Actions], Dict[str, Any]]
            ],
        ],  # Input type hint
    ) -> Callable[
        ..., AsyncIterator[Union[SentenceOutput, Dict[str, Any]]]
    ]:  # Output type hint
        @wraps(func)
        async def wrapper(
            *args, **kwargs
        ) -> AsyncIterator[Union[SentenceOutput, Dict[str, Any]]]:  # Yield type hint
            stream = func(*args, **kwargs)
            config = tts_preprocessor_config or TTSPreprocessorConfig()

            async for item in stream:
                if (
                    isinstance(item, tuple)
                    and len(item) == 3
                    and isinstance(item[1], DisplayText)
                ):
                    sentence, display, actions = item
                    if any(tag.name == "think" for tag in sentence.tags):
                        tts = ""
                    else:
                        tts = filter_text(
                            text=display.text,
                            remove_special_char=config.remove_special_char,
                            ignore_brackets=config.ignore_brackets,
                            ignore_parentheses=config.ignore_parentheses,
                            ignore_asterisks=config.ignore_asterisks,
                            ignore_angle_brackets=config.ignore_angle_brackets,
                        )

                    logger.debug(f"[{display.name}] display: {display.text}")
                    logger.debug(f"[{display.name}] tts: {tts}")

                    # Apply Korean post-processing
                    cleaned_display = KoreanCleaner.clean(display.text)
                    cleaned_tts = KoreanCleaner.clean(tts)

                    yield SentenceOutput(
                        display_text=DisplayText(
                            text=cleaned_display,
                            name=display.name,
                            avatar=display.avatar,
                        ),
                        tts_text=cleaned_tts,
                        actions=actions,
                    )
                elif isinstance(item, dict):
                    # Pass through dictionaries
                    yield item
                else:
                    logger.warning(f"tts_filter received unexpected type: {type(item)}")

        return wrapper

    return decorator


def chunk_grouper(max_chunks: int = 3):
    """
    Groups sentence outputs into a maximum number of chunks.
    Sends first 2 sentences immediately, then groups the rest into 1 last chunk.
    This balances latency and TTS overhead.
    """

    def decorator(
        func: Callable[..., AsyncIterator[Union[SentenceOutput, Dict[str, Any]]]]
    ) -> Callable[..., AsyncIterator[Union[SentenceOutput, Dict[str, Any]]]]:
        @wraps(func)
        async def wrapper(
            *args, **kwargs
        ) -> AsyncIterator[Union[SentenceOutput, Dict[str, Any]]]:
            stream = func(*args, **kwargs)
            chunk_count = 0
            remaining_sentences = []

            async for item in stream:
                if isinstance(item, SentenceOutput):
                    if chunk_count < max_chunks - 1:
                        # Yield immediately for first (max_chunks - 1) chunks
                        yield item
                        chunk_count += 1
                    else:
                        # Accumulate the rest
                        remaining_sentences.append(item)
                elif isinstance(item, dict):
                    # Pass through dicts (events) immediately
                    yield item
                else:
                    yield item

            if remaining_sentences:
                # Group all remaining into the last chunk
                merged_display = " ".join(
                    [s.display_text.text for s in remaining_sentences]
                )
                merged_tts = " ".join([s.tts_text for s in remaining_sentences])

                # Combine expressions (removing duplicates)
                merged_expressions = []
                for s in remaining_sentences:
                    if s.actions.expressions:
                        merged_expressions.extend(s.actions.expressions)

                # Use the first sentence's metadata
                first = remaining_sentences[0]
                yield SentenceOutput(
                    display_text=DisplayText(
                        text=merged_display,
                        name=first.display_text.name,
                        avatar=first.display_text.avatar,
                    ),
                    tts_text=merged_tts,
                    actions=Actions(expressions=list(set(merged_expressions))),
                )

        return wrapper

    return decorator
