import { prisma } from "@/lib/prisma";
import PostCard from "@/components/PostCard";
import Link from "next/link";

interface SearchParams {
  category?: string;
  page?: string;
}

const POSTS_PER_PAGE = 9;

export default async function HomePage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const page = Number(searchParams.page) || 1;
  const skip = (page - 1) * POSTS_PER_PAGE;

  const where = {
    published: true,
    ...(searchParams.category && {
      category: { slug: searchParams.category },
    }),
  };

  const [posts, totalCount, categories] = await Promise.all([
    prisma.post.findMany({
      where,
      include: {
        author: { select: { id: true, name: true, image: true } },
        category: true,
        tags: true,
        _count: { select: { comments: true } },
      },
      orderBy: { createdAt: "desc" },
      skip,
      take: POSTS_PER_PAGE,
    }),
    prisma.post.count({ where }),
    prisma.category.findMany({ orderBy: { name: "asc" } }),
  ]);

  const totalPages = Math.ceil(totalCount / POSTS_PER_PAGE);

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">ブログ</h1>

      {/* カテゴリフィルタ */}
      <div className="flex gap-2 mb-8 flex-wrap">
        <Link
          href="/"
          className={`px-4 py-2 rounded-full text-sm font-medium ${
            !searchParams.category
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          すべて
        </Link>
        {categories.map((category) => (
          <Link
            key={category.id}
            href={`/?category=${category.slug}`}
            className={`px-4 py-2 rounded-full text-sm font-medium ${
              searchParams.category === category.slug
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {category.name}
          </Link>
        ))}
      </div>

      {/* 記事グリッド */}
      {posts.length === 0 ? (
        <p className="text-gray-500 text-center py-12">記事がありません。</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}

      {/* ページネーション */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          {page > 1 && (
            <Link
              href={`/?page=${page - 1}${searchParams.category ? `&category=${searchParams.category}` : ""}`}
              className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200"
            >
              前へ
            </Link>
          )}
          <span className="px-4 py-2 text-gray-700">
            {page} / {totalPages}
          </span>
          {page < totalPages && (
            <Link
              href={`/?page=${page + 1}${searchParams.category ? `&category=${searchParams.category}` : ""}`}
              className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200"
            >
              次へ
            </Link>
          )}
        </div>
      )}
    </main>
  );
}
