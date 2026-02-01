import React from 'react';
import { 
  ArrowLeft, 
  Link as LinkIcon, 
  Share2, 
  Twitter, 
  Heart, 
  Repeat2, 
  Eye, 
  ExternalLink,
  MessageCircle,
  MoreHorizontal
} from 'lucide-react';

interface IconProps {
  size?: number;
  color?: string;
}

export const IconArrowLeft = ({ size = 16 }: IconProps) => <ArrowLeft size={size} />;
export const IconLink = ({ size = 16 }: IconProps) => <LinkIcon size={size} />;
export const IconShare = ({ size = 18 }: IconProps) => <Share2 size={size} />;
export const IconTwitter = ({ size = 20, color }: IconProps) => <Twitter size={size} color={color} />;
export const IconHeart = ({ size = 20, color }: IconProps) => <Heart size={size} color={color} fill={color ? color : 'none'} fillOpacity={0.2} />;
export const IconRepeat = ({ size = 20, color }: IconProps) => <Repeat2 size={size} color={color} />;
export const IconEye = ({ size = 20, color }: IconProps) => <Eye size={size} color={color} />;
export const IconExternalLink = ({ size = 20 }: IconProps) => <ExternalLink size={size} className="text-[#10B981]" />;
export const IconMessage = ({ size = 18 }: IconProps) => <MessageCircle size={size} />;
export const IconMore = ({ size = 18 }: IconProps) => <MoreHorizontal size={size} />;