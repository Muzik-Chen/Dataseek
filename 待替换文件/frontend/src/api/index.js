/**
 * API 模块统一导出 — ⚠️ 已弃用，仅向后兼容。
 *
 * 🚫 新代码请直接从具体模块导入：
 *    import { foodApi } from '@/api/food'
 *    import { authApi } from '@/api/auth'
 *
 * 此文件将在后续版本移除。
 */

// Request 实例（供需要直接调用的场景）
export { default as api } from './request'

// Auth
export { authApi } from './auth'
import { authApi } from './auth'
export const login = authApi.login.bind(authApi)
export const register = authApi.register.bind(authApi)
export const sendCode = authApi.sendCode.bind(authApi)

// Food
import { foodApi } from './food'
export { foodApi }
export const getFoods = foodApi.list.bind(foodApi)
export const getFoodDetail = foodApi.detail.bind(foodApi)
export const getFoodCategories = foodApi.categories.bind(foodApi)
export const recommendFoods = foodApi.recommend.bind(foodApi)

// Heritage
import { heritageApi } from './heritage'
export { heritageApi }
export const getHeritages = heritageApi.list.bind(heritageApi)
export const getHeritageDetail = heritageApi.detail.bind(heritageApi)

// Events
import { eventApi } from './event'
export { eventApi }
export const getEvents = eventApi.list.bind(eventApi)
export const getEventDetail = eventApi.detail.bind(eventApi)

// User
import { userApi } from './user'
export { userApi }
export const getUserProfile = userApi.getProfile.bind(userApi)
export const updateUserProfile = userApi.updateProfile.bind(userApi)
export const getUserFavorites = userApi.getFavorites.bind(userApi)
export const addFavorite = userApi.addFavorite.bind(userApi)
export const removeFavorite = userApi.removeFavorite.bind(userApi)

// Chat
import { chatApi } from './chat'
export { chatApi }
export const getChatHistory = chatApi.history.bind(chatApi)
export const getChatSession = chatApi.session.bind(chatApi)

// Trip
import { tripApi } from './trip'
export { tripApi }
export const createTripPlan = tripApi.create.bind(tripApi)
export const getTripPlans = tripApi.list.bind(tripApi)
export const getTripPlanDetail = tripApi.detail.bind(tripApi)
export const deleteTripPlan = tripApi.delete.bind(tripApi)

// Community
import { communityApi } from './community'
export { communityApi }
export const getPosts = communityApi.posts.bind(communityApi)
export const getPostDetail = communityApi.postDetail.bind(communityApi)
export const createPost = communityApi.create.bind(communityApi)
export const getComments = communityApi.getComments.bind(communityApi)
export const createComment = communityApi.addComment.bind(communityApi)
export const likePost = communityApi.like.bind(communityApi)
export const unlikePost = communityApi.unlike.bind(communityApi)

// Messages
import { messageApi } from './message'
export { messageApi }
export const getConversations = messageApi.conversations.bind(messageApi)
export const getMessages = messageApi.withUser.bind(messageApi)
export const sendMessage = messageApi.send.bind(messageApi)

// Dashboard
import { dashboardApi } from './dashboard'
export { dashboardApi }
export const getWeather = dashboardApi.weather.bind(dashboardApi)
export const getCrowd = dashboardApi.crowd.bind(dashboardApi)
export const getCrowdHistory = dashboardApi.crowdHistory.bind(dashboardApi)
export const getCrowdGeo = dashboardApi.crowdGeo.bind(dashboardApi)
export const getWeatherGeo = dashboardApi.weatherGeo.bind(dashboardApi)

// Hotel
import { hotelApi } from './hotel'
export { hotelApi }
export const getHotels = hotelApi.list.bind(hotelApi)
export const getHotelDetail = hotelApi.detail.bind(hotelApi)

// Admin
export { adminApi } from './admin'

// Search
export { searchApi } from './search'

// Music
export { musicApi } from './music'
