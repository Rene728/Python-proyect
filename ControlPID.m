Ra=8.3; La=1.51*10^-3; Rf=5.1; Lf=2.2*10^-3;
Ke=0.0879; Ki=0.0879; J=80.7e-6; Bn=14.14e-6;
A=J*La; B=J*Ra+Bn*La; C=Bn*Ra+Ki*Ke; D=Ki;
GR=1/20; %Relación de caja de engranaje
D=D*GR;
sistema=tf([D],[A B C])

mSI=0.10; %%Maximo sobreimpulso
Ts=0.4; %Tiempo de establecimiento
z=sqrt(log(mSI)^2/(log(mSI)^2+pi^2));
wn=4/(z*Ts);

a=5500;%5500;%5150
Kd=(A*(2*z*wn+a)-B)/D
K=((wn^2+2*z*wn*a)*A-C)/D
Kin=A*a*wn^2/D
-B/D % < Kd 
(D*A*Kin-(B+D*Kd)*C)/((B+D*Kd)*D) % < K

Gs=tf([Kd K Kin],[1 0]);
LC=Gs*sistema;
CR=LC/(1+LC);
step(CR)

1/(10*bandwidth(sistema)/2/pi)
1/(10*bandwidth(CR)/2/pi)

T=0.005
K1=K+(Kin*T/2)+Kd/T
K2=-K+(Kin*T/2)-2*Kd/T
K3=Kd/T
c2d(sistema,0.05,'zoh')
