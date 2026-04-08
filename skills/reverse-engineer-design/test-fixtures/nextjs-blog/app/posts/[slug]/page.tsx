import { prisma } from "@/lib/prisma";
import { notFound } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import Link from "next/link";
import Image from "next/image";

interface Props {
  params: { slug: string };
}

export async function generateStaticParams() {
  const posts = await prisma.post.findMany({
    where: { published: true },
    select: { slug: true },
  });
  return posts.map((post) => ({ slug: post.slug }));
}

export async function generateMetadata({ params }: Props) {
  const post = await prisma.post.findUnique({
    where: { slug: params.slug, published: true },
    select: { title: true, content: true },
  });
  if (!post) return { title: "Not Found" };
  return {
    title: post.title,
    description: post.content.slice(0, 160),
  };
}

export default async function PostDetailPage({ params }: Props) {
  const session = await getServerSession(authOptions);

  const post = await prisma.post.findUnique({
    where: { slug: params.slug, published: true },
    include: {
      author: { select: { id: true, name: true, image: true } },
      category: true,
      tags: true,
      comments: {
        include: {
          author: { select: { id: true, name: true, image: true } },
        },
        orderBy: { createdAt: "asc" },
      },
    },
  });

  if (!post) {
    notFound();
  }

  return (
    <article className="max-w-3xl mx-auto px-4 py-8">
      {/* カテゴリ */}
      {post.category && (
        <Link
          href={`/?category=${post.category.slug}`}
          className="text-blue-600 text-sm font-medium hover:underline"
        >
          {post.category.name}
        </Link>
      )}

      {/* タイトル */}
      <h1 className="text-4xl font-bold mt-2 mb-4">{post.title}</h1>

      {/* メタ情報 */}
      <div className="flex items-center gap-3 text-gray-500 text-sm mb-8">
        {post.author.image && (
          <Image
            src={post.author.image}
            alt={post.author.name ?? ""}
            width={32}
            height={32}
            className="rounded-full"
          />
        )}
        <span>{post.author.name}</span>
        <span>·</span>
        <time dateTime={post.createdAt.toISOString()}>
          {post.createdAt.toLocaleDateString("ja-JP")}
        </time>
      </div>

      {/* タグ */}
      {post.tags.length > 0 && (
        <div className="flex gap-2 mb-6 flex-wrap">
          {post.tags.map((tag) => (
            <span
              key={tag.id}
              className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
            >
              #{tag.name}
            </span>
          ))}
        </div>
      )}

      {/* 本文 */}
      <div className="prose prose-lg max-w-none mb-12">
        {post.content.split("\n").map((paragraph, i) => (
          <p key={i}>{paragraph}</p>
        ))}
      </div>

      {/* コメントセクション */}
      <section className="border-t pt-8">
        <h2 className="text-2xl font-bold mb-6">
          コメント ({post.comments.length})
        </h2>

        {/* コメント投稿フォーム */}
        {session ? (
          <form
            action={`/api/posts/${post.id}/comments`}
            method="POST"
            className="mb-8"
          >
            <textarea
              name="content"
              placeholder="コメントを入力..."
              rows={4}
              required
              className="w-full border rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              className="mt-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              コメントを投稿
            </button>
          </form>
        ) : (
          <p className="mb-8 text-gray-500">
            コメントするには{" "}
            <Link href="/api/auth/signin" className="text-blue-600 hover:underline">
              ログイン
            </Link>{" "}
            が必要です。
          </p>
        )}

        {/* コメント一覧 */}
        <div className="space-y-4">
          {post.comments.map((comment) => (
            <div key={comment.id} className="flex gap-3">
              {comment.author.image && (
                <Image
                  src={comment.author.image}
                  alt={comment.author.name ?? ""}
                  width={40}
                  height={40}
                  className="rounded-full flex-shrink-0"
                />
              )}
              <div className="flex-1 bg-gray-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-medium text-sm">{comment.author.name}</span>
                  <time className="text-gray-400 text-xs">
                    {comment.createdAt.toLocaleDateString("ja-JP")}
                  </time>
                </div>
                <p className="text-gray-700 text-sm">{comment.content}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </article>
  );
}
