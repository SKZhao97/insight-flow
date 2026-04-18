type LoadingViewProps = {
  label?: string;
};

type ErrorViewProps = {
  message: string;
};

export function LoadingView({ label = "Loading resource" }: LoadingViewProps) {
  return <div className="state-view">{label}...</div>;
}

export function ErrorView({ message }: ErrorViewProps) {
  return <div className="state-view is-error">{message}</div>;
}
