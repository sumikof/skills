import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import { redirect } from "next/navigation";
import { prisma } from "@/lib/prisma";
import Link from "next/link";

export const metadata = {
  title: "ダッシュボード",
};

export default async function DashboardPage() {
  const session = await getServerSession(authOptions);

  if (!session?.user?.email) {
    redirect("/api/auth/signin?callbackUrl=/dashboard");
  }

  const user = await prisma.user.findUnique({
    where: { email: session.user.email },
    include: {
      posts: {
        include: {
          category: true,
          _count: { select: { comments: true } },
        },
        orderBy: { updatedAt: "desc" },
      },
      _count: { select: { posts: true, comments: true } },
    },
  });

  if (!user) {
    redirect("/api/auth/signin");
  }

  const publishedCount = user.posts.filter((p) => p.published).length;
  const draftCount = user.posts.filter((p) => !p.published).length;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">ダッシュボード</h1>
        <Link
          href="/dashboard/posts/new"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          新規投稿
        </Link>
      </div>

      {/* 統計カード */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white border rounded-lg p-6">
          <p className="text-sm text-gray-500 mb-1">総記事数</p>
          <p className="text-3xl font-bold">{user._count.posts}</p>
        </div>
        <div className="bg-white border rounded-lg p-6">
          <p className="text-sm text-gray-500 mb-1">公開済み</p>
          <p className="text-3xl font-bold text-green-600">{publishedCount}</p>
        </div>
        <div className="bg-white border rounded-lg p-6">
          <p className="text-sm text-gray-500 mb-1">下書き</p>
          <p className="text-3xl font-bold text-yellow-600">{draftCount}</p>
        </div>
      </div>

      {/* 記事一覧 */}
      <div className="bg-white border rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b">
          <h2 className="font-semibold text-lg">記事管理</h2>
        </div>

        {user.posts.length === 0 ? (
          <p className="text-center text-gray-500 py-12">
            まだ記事がありません。
          </p>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  タイトル
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  カテゴリ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  ステータス
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  コメント
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  更新日
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {user.posts.map((post) => (
                <tr key={post.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <Link
                      href={`/posts/${post.slug}`}
                      className="font-medium text-gray-900 hover:text-blue-600 line-clamp-1"
                    >
                      {post.title}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {post.category?.name ?? "—"}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        post.published
                          ? "bg-green-100 text-green-800"
                          : "bg-yellow-100 text-yellow-800"
                      }`}
                    >
                      {post.published ? "公開" : "下書き"}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {post._count.comments}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {post.updatedAt.toLocaleDateString("ja-JP")}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2">
                      <Link
                        href={`/dashboard/posts/${post.id}/edit`}
                        className="text-sm text-blue-600 hover:underline"
                      >
                        編集
                      </Link>
                      <button
                        className="text-sm text-red-600 hover:underline"
                        data-post-id={post.id}
                      >
                        削除
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
