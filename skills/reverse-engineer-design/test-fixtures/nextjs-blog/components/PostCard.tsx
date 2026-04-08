import Link from "next/link";
import Image from "next/image";

interface PostCardProps {
  post: {
    id: string;
    title: string;
    slug: string;
    content: string;
    createdAt: Date;
    author: {
      id: string;
      name: string | null;
      image: string | null;
    };
    category: {
      id: string;
      name: string;
      slug: string;
    } | null;
    tags: {
      id: string;
      name: string;
      slug: string;
    }[];
    _count: {
      comments: number;
    };
  };
}

export default function PostCard({ post }: PostCardProps) {
  const excerpt = post.content.slice(0, 150) + (post.content.length > 150 ? "..." : "");

  return (
    <article className="bg-white border rounded-xl overflow-hidden hover:shadow-md transition-shadow">
      {/* カード本体 */}
      <div className="p-6">
        {/* カテゴリバッジ */}
        {post.category && (
          <Link
            href={`/?category=${post.category.slug}`}
            className="inline-block text-xs font-semibold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full mb-3 hover:bg-blue-100"
          >
            {post.category.name}
          </Link>
        )}

        {/* タイトル */}
        <h2 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2">
          <Link href={`/posts/${post.slug}`} className="hover:text-blue-600">
            {post.title}
          </Link>
        </h2>

        {/* 抜粋 */}
        <p className="text-gray-500 text-sm line-clamp-3 mb-4">{excerpt}</p>

        {/* タグ */}
        {post.tags.length > 0 && (
          <div className="flex gap-1.5 flex-wrap mb-4">
            {post.tags.slice(0, 3).map((tag) => (
              <span
                key={tag.id}
                className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded"
              >
                #{tag.name}
              </span>
            ))}
            {post.tags.length > 3 && (
              <span className="text-xs text-gray-400">+{post.tags.length - 3}</span>
            )}
          </div>
        )}

        {/* フッター */}
        <div className="flex items-center justify-between pt-4 border-t">
          {/* 著者情報 */}
          <div className="flex items-center gap-2">
            {post.author.image ? (
              <Image
                src={post.author.image}
                alt={post.author.name ?? ""}
                width={28}
                height={28}
                className="rounded-full"
              />
            ) : (
              <div className="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium text-gray-600">
                {post.author.name?.charAt(0) ?? "U"}
              </div>
            )}
            <span className="text-sm text-gray-600 font-medium">
              {post.author.name ?? "匿名"}
            </span>
          </div>

          {/* メタ情報 */}
          <div className="flex items-center gap-3 text-xs text-gray-400">
            <time dateTime={new Date(post.createdAt).toISOString()}>
              {new Date(post.createdAt).toLocaleDateString("ja-JP")}
            </time>
            <span className="flex items-center gap-1">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-3.5 w-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              {post._count.comments}
            </span>
          </div>
        </div>
      </div>
    </article>
  );
}
