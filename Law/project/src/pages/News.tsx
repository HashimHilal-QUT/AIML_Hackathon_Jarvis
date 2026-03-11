import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';
import { ThumbsUp, MessageSquare, Share2, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface Post {
  id: string;
  title: string;
  content: string;
  author: {
    id: string;
    full_name: string;
    role: string;
  };
  likes_count: number;
  comments_count: number;
  created_at: string;
  has_liked?: boolean;
}

export default function News() {
  const { user } = useAuth();
  const [posts, setPosts] = useState<Post[]>([]);
  const [newPost, setNewPost] = useState({ title: '', content: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchPosts();
  }, []);

  async function fetchPosts() {
    if (!supabase) return;

    const { data, error } = await supabase
      .from('posts')
      .select(`
        *,
        author:users(id, full_name, role)
      `)
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error fetching posts:', error);
      return;
    }

    if (user) {
      const { data: likes } = await supabase
        .from('likes')
        .select('post_id')
        .eq('user_id', user.id);

      const likedPostIds = new Set(likes?.map(like => like.post_id));
      
      setPosts(data.map(post => ({
        ...post,
        has_liked: likedPostIds.has(post.id)
      })));
    } else {
      setPosts(data);
    }
  }

  async function handleSubmitPost(e: React.FormEvent) {
    e.preventDefault();
    if (!supabase || !user || !newPost.title.trim() || !newPost.content.trim()) return;

    setIsSubmitting(true);

    try {
      const { error } = await supabase
        .from('posts')
        .insert([
          {
            title: newPost.title,
            content: newPost.content,
            author_id: user.id,
          }
        ]);

      if (error) throw error;

      setNewPost({ title: '', content: '' });
      fetchPosts();
    } catch (error) {
      console.error('Error creating post:', error);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLike(postId: string) {
    if (!supabase || !user) return;

    const post = posts.find(p => p.id === postId);
    if (!post) return;

    try {
      if (post.has_liked) {
        await supabase
          .from('likes')
          .delete()
          .eq('post_id', postId)
          .eq('user_id', user.id);
      } else {
        await supabase
          .from('likes')
          .insert([{ post_id: postId, user_id: user.id }]);
      }

      fetchPosts();
    } catch (error) {
      console.error('Error toggling like:', error);
    }
  }

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Legal News & Updates</h1>

      {user && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Create a Post</h2>
          <form onSubmit={handleSubmitPost} className="space-y-4">
            <div>
              <input
                type="text"
                placeholder="Post title"
                value={newPost.title}
                onChange={(e) => setNewPost(prev => ({ ...prev, title: e.target.value }))}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
            </div>
            <div>
              <textarea
                placeholder="What would you like to share?"
                value={newPost.content}
                onChange={(e) => setNewPost(prev => ({ ...prev, content: e.target.value }))}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 h-32 resize-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Posting...' : 'Post'}
            </button>
          </form>
        </div>
      )}

      <div className="space-y-6">
        {posts.map((post) => (
          <article key={post.id} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-semibold mb-2">{post.title}</h2>
                <div className="flex items-center text-sm text-gray-500 space-x-2">
                  <span className="font-medium">{post.author.full_name}</span>
                  <span>•</span>
                  <span className="capitalize">{post.author.role}</span>
                  <span>•</span>
                  <span className="flex items-center">
                    <Clock className="h-4 w-4 mr-1" />
                    {formatDistanceToNow(new Date(post.created_at), { addSuffix: true })}
                  </span>
                </div>
              </div>
            </div>

            <p className="text-gray-700 mb-4">{post.content}</p>

            <div className="flex items-center space-x-6 text-gray-500">
              <button
                onClick={() => handleLike(post.id)}
                className={`flex items-center space-x-1 ${
                  post.has_liked ? 'text-indigo-600' : ''
                }`}
              >
                <ThumbsUp className="h-5 w-5" />
                <span>{post.likes_count}</span>
              </button>
              <button className="flex items-center space-x-1">
                <MessageSquare className="h-5 w-5" />
                <span>{post.comments_count}</span>
              </button>
              <button className="flex items-center space-x-1">
                <Share2 className="h-5 w-5" />
                <span>Share</span>
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}