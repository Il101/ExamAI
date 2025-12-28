'use client';

import { createReactBlockSpec } from '@blocknote/react';
import { CheckYourself } from './check-yourself';
import { defaultProps } from '@blocknote/core';

/**
 * Custom MCQ (Multiple Choice Quiz) block for BlockNote
 * Integrates the existing CheckYourself component as a block
 */
export const MCQBlock = createReactBlockSpec(
    {
        type: 'mcq',
        propSchema: {
            topicId: {
                default: '',
            },
            examId: {
                default: '',
            },
            quizCompleted: {
                default: false,
            },
        },
        content: 'none', // MCQ block has no editable content
    },
    {
        render: (props) => {
            const { block } = props;
            const topicId = block.props.topicId as string;
            const examId = block.props.examId as string;

            if (!topicId) {
                return (
                    <div className="p-4 border border-dashed rounded-lg bg-muted/20 text-center text-sm text-muted-foreground">
                        MCQ Quiz block (Topic ID not set)
                    </div>
                );
            }

            return (
                <div className="my-6">
                    <CheckYourself
                        topicId={topicId}
                        examId={examId}
                        onComplete={(score, total) => {
                            console.log('Quiz completed:', score, '/', total);
                            // Update block props to mark as completed
                            props.editor.updateBlock(block, {
                                props: {
                                    ...block.props,
                                    quizCompleted: true,
                                },
                            });
                        }}
                        onSkip={() => {
                            console.log('Quiz skipped');
                            props.editor.updateBlock(block, {
                                props: {
                                    ...block.props,
                                    quizCompleted: true,
                                },
                            });
                        }}
                    />
                </div>
            );
        },
    }
);
