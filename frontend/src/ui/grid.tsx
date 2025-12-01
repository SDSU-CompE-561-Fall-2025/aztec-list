import Card from "./card";

export default function Grid() {
    return (
        <div className="grid justify-center gap-4 grid-cols-[repeat(auto-fit,minmax(250px,1fr))]">
            <Card/>
            <Card/>
            <Card/>
            <Card/>
            <Card/>
            <Card/>
            <Card/>    
        </div>
    ) 
};