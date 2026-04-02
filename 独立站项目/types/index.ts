/**
 * 高端生鲜独立站 V3.0 — TypeScript 类型定义
 * 文档版本：v1.1
 * 来源：docs/plans/2026-03-29-生鲜独立站技术规范.md
 * 用途：Next.js 前端 + Strapi API 联调类型保障
 * 使用方式：直接 import from '@/types'
 */

// ─────────────────────────────────────────
// Strapi API 响应包装
// ─────────────────────────────────────────

export interface StrapiResponse<T> {
  data: T;
  meta: {
    pagination?: {
      page: number;
      pageSize: number;
      pageCount: number;
      total: number;
    };
  };
}

export interface StrapiMedia {
  id: number;
  url: string;
  alternativeText: string | null;
  width: number;
  height: number;
  formats?: {
    thumbnail?: { url: string; width: number; height: number };
    small?: { url: string; width: number; height: number };
    medium?: { url: string; width: number; height: number };
  };
}

// ─────────────────────────────────────────
// SEO 元数据组件
// ─────────────────────────────────────────

export interface SeoMetadata {
  metaTitle: string;
  metaDescription: string;
  metaKeywords: string[];
  ogImage?: StrapiMedia;
  canonicalUrl?: string;
  noIndex?: boolean;
}

// ─────────────────────────────────────────
// 营养成分组件
// ─────────────────────────────────────────

export interface NutritionFacts {
  calories: number;       // 每100g，千卡
  protein: number;        // 克
  fat: number;           // 克
  carbohydrates: number;  // 克
  fiber: number;         // 克
  vitaminC?: number;      // 毫克
  potassium?: number;     // 毫克
}

// ─────────────────────────────────────────
// 用户评价组件（DynamicZone 内嵌）
// ─────────────────────────────────────────

export interface UserReview {
  id: string;
  nickname: string;
  avatar?: StrapiMedia;
  content: string;
  rating?: 4 | 5;         // 仅接受 4-5 星
  city?: string;          // 评价来源城市
  createdAt: string;
}

// ─────────────────────────────────────────
// 城市管家
// ─────────────────────────────────────────

export interface CityManager {
  id: number;
  name: string;           // 如"小沪"
  weComQrCode: StrapiMedia;
  weComId?: string;
  intro?: string;
  isActive: boolean;
}

// ─────────────────────────────────────────
// 城市落地页（CityPage）
// ─────────────────────────────────────────

export interface CityPage {
  id: number;
  cityName: string;       // 如"上海"
  slug: string;           // 如"shanghai-fresh"
  province: Province;
  localIntro: string;     // Markdown 富文本
  localSpots: string[];   // 如["陆家嘴","古北"]
  deliveryTime: string;   // 如"最快 2 小时达"
  heroProduct: string;    // 如"即食牛油果"
  userReviews: UserReview[];
  heroImage: StrapiMedia;
  galleryImages?: StrapiMedia[];
  seoMetadata: SeoMetadata;
  manager: CityManager;
  isActive: boolean;
  publishedAt: string | null;
}

export type Province =
  | '华北' | '东北' | '华东'
  | '华中' | '华南' | '西南' | '西北';

// ─────────────────────────────────────────
// 文章（Article）
// ─────────────────────────────────────────

export interface Article {
  id: number;
  title: string;
  slug: string;
  category: '科普' | '食谱' | '动态';
  summary: string;        // ≤150字，用于 Meta Description
  content: string;        // Markdown 正文
  coverImage: StrapiMedia;
  relatedProducts?: Product[];
  cityScope?: CityScope;
  isAiGenerated: boolean;
  aiPromptUsed?: string;
  author: string;
  readingTime?: number;   // 分钟
  publishedAt: string | null;
}

export type CityScope =
  | '全国'
  | Province
  | CityPage['slug'];

// ─────────────────────────────────────────
// 产品（Product）
// ─────────────────────────────────────────

export interface Product {
  id: number;
  name: string;
  slug: string;
  category: ProductCategory;
  origin: string;         // 如"墨西哥米却肯"
  grade: ProductGrade;
  description: string;    // Markdown 富文本
  nutritionFacts?: NutritionFacts;
  price?: number;         // 参考价（不展示购买入口）
  images: StrapiMedia[];
  certifications?: string[];
  storageMethod?: string;
  shelfLife?: string;
  seoMetadata: SeoMetadata;
  publishedAt: string | null;
}

export type ProductCategory =
  | '牛油果'
  | '浆果'
  | '热带水果'
  | '其他';

export type ProductGrade = 'A级' | 'AA级' | '特选级';

// ─────────────────────────────────────────
// 留资记录（LeadSubmission，系统自动创建）
// ─────────────────────────────────────────

export interface LeadSubmission {
  id: number;
  phone: string;
  name?: string;
  healthGoals?: HealthGoal[];
  sourcePage: string;
  sourceCity?: string;
  createdAt: string;
  status: 'new' | 'contacted' | 'converted';
}

export type HealthGoal =
  | '减脂增肌'
  | '孕期营养'
  | '抗衰老'
  | '日常养生'
  | '其他';

// ─────────────────────────────────────────
// 前端 Props 类型（Next.js App Router）
// ─────────────────────────────────────────

export interface HomePageProps {
  latestArticles: Article[];
  featuredProducts: Product[];
  globalSeo: SeoMetadata;
}

export interface CityPageProps {
  city: CityPage;
  relatedProducts: Product[];
  localArticles: Article[];
}

export interface ProductDetailPageProps {
  product: Product;
  relatedProducts: Product[];
}

export interface BlogListPageProps {
  articles: Article[];
  pagination: StrapiResponse<null>['meta']['pagination'];
}

export interface BlogDetailPageProps {
  article: Article;
  relatedProducts: Product[];
}

// ─────────────────────────────────────────
// JSON-LD 类型（结构化数据）
// ─────────────────────────────────────────

export interface OrganizationJsonLd {
  '@context': 'https://schema.org';
  '@type': 'Organization';
  name: string;
  url: string;
  logo: string;
  sameAs: string[];
}

export interface LocalBusinessJsonLd {
  '@context': 'https://schema.org';
  '@type': 'LocalBusiness';
  name: string;
  address: { '@type': 'PostalAddress'; addressLocality: string };
  areaServed: string;
  priceRange: '¥¥¥';
  openingHours: 'Mo-Su 08:00-22:00';
}

export interface ProductJsonLd {
  '@context': 'https://schema.org';
  '@type': 'Product';
  name: string;
  image: string;
  description: string;
  brand: { '@type': 'Brand'; name: string };
  offers: { '@type': 'Offer'; price: string; priceCurrency: 'CNY' };
}

export interface ArticleJsonLd {
  '@context': 'https://schema.org';
  '@type': 'Article';
  headline: string;
  image: string;
  author: { '@type': 'Person'; name: string };
  datePublished: string;
  publisher: { '@type': 'Organization'; name: string };
}

export interface BreadcrumbJsonLd {
  '@context': 'https://schema.org';
  '@type': 'BreadcrumbList';
  itemListElement: Array<{
    '@type': 'ListItem';
    position: number;
    name: string;
    item: string;
  }>;
}

// ─────────────────────────────────────────
// 企微 Widget 埋点事件
// ─────────────────────────────────────────

export interface WeComTrackingEvents {
  'wecom_qr_shown': { citySlug: string; managerName: string };
  'wecom_qr_clicked': { citySlug: string; managerName: string };
  'wecom_qr_expanded': { citySlug: string; managerName: string };
}

// ─────────────────────────────────────────
// 留资表单请求/响应
// ─────────────────────────────────────────

export interface LeadFormRequest {
  phone: string;
  name?: string;
  healthGoals?: HealthGoal[];
  sourcePage: string;
  sourceCity?: string;
}

export interface LeadFormResponse {
  success: boolean;
  message: string;
  weComQrUrl?: string;
  managerName?: string;
}
