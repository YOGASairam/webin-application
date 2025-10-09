from fastapi import FastAPI
import models
from database import engine
from routers import auth,products,users,admin,orders
from dependencies import get_current_admin_user, get_current_user
from fastapi import Depends



app = FastAPI()


models.Base.metadata.create_all(bind=engine)
# import pdb;pdb.set_trace()

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/products", tags=["Products"],dependencies=[Depends(get_current_user)])
app.include_router(users.router, prefix="/user", tags=["Users"],dependencies=[Depends(get_current_user)])
app.include_router(admin.router, prefix="/admin", tags=["Admin"],dependencies=[Depends(get_current_admin_user)])
app.include_router(orders.router, prefix="/orders", tags=["Orders"],dependencies=[Depends(get_current_user)])

