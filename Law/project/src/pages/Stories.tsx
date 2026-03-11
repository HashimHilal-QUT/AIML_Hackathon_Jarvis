import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';
import { Heart, ThumbsUp, MessageSquare, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface Story {
  id: string;
  title: string;
  content: string;
  impact: string;
  created_at: string;
  lawyer: {
    id: string;
    user: {
      full_name: string;
    };
  };
  _count: {
    likes: number;
    loves: number;
    comments: number;
  };
  has_liked?: boolean;
  has_loved?: boolean;
}

export default function Stories() {
  const { user } = useAuth();
  const [stories, setStories] = useState<Story[]>([]);
  const [selectedStory, setSelectedStory] = useState<string | null>(null);
  const [comment, setComment] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchStories();
  }, [user]);

  async function fetchStories() {
    if (!supabase) return;

    try {
      // First, get all stories with their basic info and counts
      const { data: storiesData, error: storiesError } = await supabase
        .from('stories')
        .select(`
          *,
          lawyer:lawyers(
            id,
            user:users(full_name)
          )
        `)
        .order('created_at', { ascending: false });

      if (storiesError) throw storiesError;

      // If user is authenticated, get their reactions
      let userReactions = [];
      if (user) {
        const { data: reactionsData } = await supabase
          .from('story_reactions')
          .select('story_id, type')
          .eq('user_id', user.id);
        userReactions = reactionsData || [];
      }

      // Get reaction counts for all stories
      const { data: reactionsCount } = await supabase
        .from('story_reactions')
        .select('story_id, type')
        .in('story_id', storiesData.map(s => s.id));

      // Get comment counts
      const { data: commentsCount } = await supabase
        .from('story_comments')
        .select('story_id')
        .in('story_id', storiesData.map(s => s.id));

      // Process and combine all the data
      const processedStories = storiesData.map(story => ({
        ...story,
        _count: {
          likes: (reactionsCount || []).filter(r => r.story_id === story.id && r.type === 'like').length,
          loves: (reactionsCount || []).filter(r => r.story_id === story.id && r.type === 'love').length,
          comments: (commentsCount || []).filter(c => c.story_id === story.id).length
        },
        has_liked: userReactions.some(r => r.story_id === story.id && r.type === 'like'),
        has_loved: userReactions.some(r => r.story_id === story.id && r.type === 'love')
      }));

      setStories(processedStories);
    } catch (error) {
      console.error('Error fetching stories:', error);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleReaction(storyId: string, type: 'like' | 'love') {
    if (!supabase || !user) {
      alert('Please sign in to react to stories');
      return;
    }

    const story = stories.find(s => s.id === storyId);
    if (!story) return;

    const hasReacted = type === 'like' ? story.has_liked : story.has_loved;

    try {
      if (hasReacted) {
        await supabase
          .from('story_reactions')
          .delete()
          .eq('story_id', storyId)
          .eq('user_id', user.id)
          .eq('type', type);
      } else {
        await supabase
          .from('story_reactions')
          .upsert([{
            story_id: storyId,
            user_id: user.id,
            type
          }]);
      }

      fetchStories();
    } catch (error) {
      console.error('Error toggling reaction:', error);
    }
  }

  async function handleComment(storyId: string) {
    if (!supabase || !user) {
      alert('Please sign in to comment');
      return;
    }

    if (!comment.trim()) return;

    try {
      await supabase
        .from('story_comments')
        .insert([{
          story_id: storyId,
          user_id: user.id,
          content: comment.trim()
        }]);

      setComment('');
      setSelectedStory(null);
      fetchStories();
    } catch (error) {
      console.error('Error adding comment:', error);
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Success Stories</h1>

      {stories.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600">No success stories have been shared yet.</p>
        </div>
      ) : (
        <div className="space-y-8">
          {stories.map((story) => (
            <article key={story.id} className="bg-white rounded-lg shadow-lg overflow-hidden">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900 mb-2">{story.title}</h2>
                    <div className="flex items-center text-sm text-gray-500 space-x-2">
                      <span className="font-medium">{story.lawyer.user.full_name}</span>
                      <span>•</span>
                      <span className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        {formatDistanceToNow(new Date(story.created_at), { addSuffix: true })}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="prose max-w-none mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Case Details</h3>
                  <p className="text-gray-700 mb-4">{story.content}</p>
                  
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Client Impact</h3>
                  <p className="text-gray-700">{story.impact}</p>
                </div>

                <div className="flex items-center space-x-6 text-gray-500">
                  <button
                    onClick={() => handleReaction(story.id, 'like')}
                    className={`flex items-center space-x-1 transition-colors ${
                      story.has_liked ? 'text-indigo-600' : 'hover:text-indigo-600'
                    }`}
                  >
                    <ThumbsUp className="h-5 w-5" />
                    <span>{story._count.likes}</span>
                  </button>
                  <button
                    onClick={() => handleReaction(story.id, 'love')}
                    className={`flex items-center space-x-1 transition-colors ${
                      story.has_loved ? 'text-red-600' : 'hover:text-red-600'
                    }`}
                  >
                    <Heart className="h-5 w-5" />
                    <span>{story._count.loves}</span>
                  </button>
                  <button
                    onClick={() => setSelectedStory(selectedStory === story.id ? null : story.id)}
                    className="flex items-center space-x-1 hover:text-indigo-600 transition-colors"
                  >
                    <MessageSquare className="h-5 w-5" />
                    <span>{story._count.comments}</span>
                  </button>
                </div>

                {selectedStory === story.id && (
                  <div className="mt-6 pt-6 border-t">
                    <textarea
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      placeholder="Share your thoughts..."
                      className="w-full rounded-lg border border-gray-300 px-4 py-2 h-24 resize-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                    <div className="flex justify-end mt-2 space-x-2">
                      <button
                        onClick={() => setSelectedStory(null)}
                        className="px-4 py-2 text-gray-600 hover:text-gray-800"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleComment(story.id)}
                        disabled={!comment.trim()}
                        className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Comment
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}