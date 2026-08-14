import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function IconBase({ children, ...props }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export const HomeIcon = (props: IconProps) => (
  <IconBase {...props}><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z" /></IconBase>
);
export const SparkIcon = (props: IconProps) => (
  <IconBase {...props}><path d="M12 3 10.8 7.8 6 9l4.8 1.2L12 15l1.2-4.8L18 9l-4.8-1.2Z" /><path d="m18 15-.6 2.4L15 18l2.4.6L18 21l.6-2.4L21 18l-2.4-.6Z" /></IconBase>
);
export const TopicIcon = (props: IconProps) => (
  <IconBase {...props}><path d="M4 5h16M4 12h12M4 19h8" /><circle cx="19" cy="12" r="2" /></IconBase>
);
export const PipelineIcon = (props: IconProps) => (
  <IconBase {...props}><rect x="3" y="4" width="5" height="16" rx="1" /><rect x="10" y="4" width="5" height="10" rx="1" /><rect x="17" y="4" width="4" height="7" rx="1" /></IconBase>
);
export const CalendarIcon = (props: IconProps) => (
  <IconBase {...props}><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></IconBase>
);
export const ChartIcon = (props: IconProps) => (
  <IconBase {...props}><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></IconBase>
);
export const ReviewIcon = (props: IconProps) => (
  <IconBase {...props}><path d="M5 3h11l3 3v15H5Z" /><path d="M16 3v4h4M8 12h8M8 16h6" /></IconBase>
);
export const SettingsIcon = (props: IconProps) => (
  <IconBase {...props}><circle cx="12" cy="12" r="3" /><path d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.4-2.4 1A7 7 0 0 0 14.8 6L14.5 3h-5L9.2 6a7 7 0 0 0-1.7 1.1l-2.4-1-2 3.4 2 1.5A7 7 0 0 0 5 12c0 .3 0 .7.1 1l-2 1.5 2 3.4 2.4-1A7 7 0 0 0 9.2 18l.3 3h5l.3-3a7 7 0 0 0 1.7-1.1l2.4 1 2-3.4-2-1.5c.1-.3.1-.7.1-1Z" /></IconBase>
);
export const PlusIcon = (props: IconProps) => (
  <IconBase {...props}><path d="M12 5v14M5 12h14" /></IconBase>
);
