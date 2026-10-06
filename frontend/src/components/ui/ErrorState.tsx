export default function ErrorState({ message }: { message: string }) {
  return (
    <div className="state error" role="alert">
      {message}
    </div>
  );
}
